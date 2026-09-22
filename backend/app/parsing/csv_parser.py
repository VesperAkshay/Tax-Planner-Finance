import io
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

from app.parsing.balance_reconciler import reconcile_statement_balance
from app.parsing.constants import DEFAULT_REVIEW_THRESHOLD
from app.parsing.csv_adapter_schema import BankAdapterConfig, SignConvention
from app.parsing.pdf_parser import parse_date, parse_numeric
from app.parsing.schemas import ParsedTransactionRow, StatementParseResult


class CSVBankAdapterRegistry:
    """
    Registry that loads and manages BankAdapterConfig specifications from JSON files,
    supporting both explicit bank_id lookup and automated header-sniffing.
    """

    def __init__(self, adapters_dir: Optional[Path] = None):
        if adapters_dir is None:
            adapters_dir = Path(__file__).resolve().parent / "adapters"
        self.adapters_dir = adapters_dir
        self.adapters: Dict[str, BankAdapterConfig] = {}
        self.load_adapters()

    def load_adapters(self) -> None:
        """Loads and validates all adapter JSON files in the adapters directory."""
        self.adapters.clear()
        if not self.adapters_dir.exists():
            return

        for path in self.adapters_dir.glob("*.json"):
            if path.name == "schema.json":
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                config = BankAdapterConfig.model_validate(data)
                self.adapters[config.bank_id] = config
            except Exception as e:
                # Log or ignore invalid config files during scan
                print(f"Warning: Failed to load bank adapter from {path}: {e}")

    def get(self, bank_id: str) -> Optional[BankAdapterConfig]:
        """Lookup an adapter by bank_id or bank aliases."""
        clean_id = bank_id.lower().strip()
        if clean_id in self.adapters:
            return self.adapters[clean_id]
        for k, v in self.adapters.items():
            if k.startswith(clean_id) or clean_id.startswith(k) or clean_id in v.bank_name.lower():
                return v
        return None

    def sniff(self, content_sample: str) -> Optional[Tuple[BankAdapterConfig, float]]:
        """
        Sniffs the best-matching bank adapter from a sample of lines from the CSV.
        Returns (best_adapter, match_score) or None.
        """
        lines = [line.strip() for line in content_sample.splitlines() if line.strip()]
        if not lines:
            return None

        best_adapter: Optional[BankAdapterConfig] = None
        best_score = 0.0

        for adapter in self.adapters.values():
            if not adapter.header_signatures:
                continue

            # Check matching signatures line by line
            for line in lines[:30]:  # inspect first 30 lines
                matches = 0
                for sig in adapter.header_signatures:
                    if sig.lower() in line.lower():
                        matches += 1

                score = matches / len(adapter.header_signatures)
                if score > best_score and score >= 0.5:
                    best_score = score
                    best_adapter = adapter

        if best_adapter and best_score >= 0.5:
            return best_adapter, best_score
        return None


class CSVBankParser:
    """
    Parser for bank statement CSV exports.
    Utilizes bank adapters to normalize diverse bank CSV structures into standard ParsedTransactionRows.
    """

    def __init__(self, registry: Optional[CSVBankAdapterRegistry] = None):
        self.registry = registry or CSVBankAdapterRegistry()

    def _locate_header_row(
        self, lines: List[str], adapter: BankAdapterConfig
    ) -> int:
        """Finds the 0-indexed line containing the column headers."""
        if adapter.header_row_identifier:
            target = adapter.header_row_identifier.lower()
            for idx, line in enumerate(lines[:50]):
                if target in line.lower():
                    return idx

        # Fallback: look for the line with highest matching signatures
        best_idx = None
        max_matches = 0
        date_col_lower = adapter.date_column.lower()

        for idx, line in enumerate(lines[:50]):
            line_lower = line.lower()
            if date_col_lower in line_lower:
                matches = sum(1 for sig in adapter.header_signatures if sig.lower() in line_lower)
                if matches > max_matches:
                    max_matches = matches
                    best_idx = idx

        if best_idx is not None and max_matches >= 2:
            return best_idx

        # Fallback to configured skip_rows
        return adapter.skip_rows

    def parse(
        self,
        file_path: Union[str, Path],
        bank_id: Optional[str] = None,
        encoding: str = "utf-8",
        custom_mapping: Optional[Dict[str, str]] = None,
    ) -> StatementParseResult:
        """
        Parses a bank CSV file into a StatementParseResult.
        If bank_id is omitted, automatically sniffs the format.
        Supports custom_mapping for user-defined column mappings (Task 16.3).
        """
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        with open(path, "r", encoding=encoding, errors="replace") as f:
            raw_content = f.read()

        return self.parse_content(
            content=raw_content,
            file_name=path.name,
            file_path=str(path),
            bank_id=bank_id,
            custom_mapping=custom_mapping,
        )

    def parse_content(
        self,
        content: str,
        file_name: str = "statement.csv",
        file_path: str = "",
        bank_id: Optional[str] = None,
        custom_mapping: Optional[Dict[str, str]] = None,
    ) -> StatementParseResult:
        """Parses CSV raw string content with optional custom column mapping (Task 16.3)."""
        result = StatementParseResult(
            file_path=file_path,
            file_name=file_name,
            file_type="csv",
            is_scanned=False,
        )

        adapter: Optional[BankAdapterConfig] = None
        if custom_mapping:
            has_separate = bool(custom_mapping.get("debit") or custom_mapping.get("credit"))
            has_type = bool(custom_mapping.get("type"))
            if has_separate:
                sign_conv = SignConvention.SEPARATE_COLUMNS
            elif has_type:
                sign_conv = SignConvention.TYPE_INDICATOR
            else:
                sign_conv = SignConvention.SIGNED_AMOUNT

            adapter = BankAdapterConfig(
                bank_id="custom_mapping",
                bank_name="Custom User Mapping",
                date_column=custom_mapping.get("date", "Date"),
                description_column=custom_mapping.get("description", "Description"),
                amount_column=custom_mapping.get("amount"),
                debit_column=custom_mapping.get("debit"),
                credit_column=custom_mapping.get("credit"),
                type_column=custom_mapping.get("type"),
                balance_column=custom_mapping.get("balance"),
                reference_column=custom_mapping.get("reference"),
                sign_convention=sign_conv,
                header_signatures=[],
                header_row_identifier=custom_mapping.get("date"),
            )
        elif bank_id:
            adapter = self.registry.get(bank_id)
            if not adapter:
                result.warnings.append(f"Specified bank_id '{bank_id}' not found in registry.")

        if not adapter:
            sniff_res = self.registry.sniff(content)
            if sniff_res:
                adapter, score = sniff_res

        if not adapter:
            # Extract available column headers for user fallback guidance (Task 16.3)
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            first_line = lines[0] if lines else ""
            available_cols = [c.strip() for c in first_line.split(",") if c.strip()]
            cols_lower = {c.lower(): c for c in available_cols}

            # Smart generic standard CSV auto-fallback:
            has_date = any(k in cols_lower for k in ["date", "transaction date", "txn date", "value date"])
            has_desc = any(k in cols_lower for k in ["description", "narration", "particulars", "remarks"])
            has_debit_credit = ("debit" in cols_lower or "withdrawal" in cols_lower or "withdrawal amt." in cols_lower) and ("credit" in cols_lower or "deposit" in cols_lower or "deposit amt." in cols_lower)
            has_amount = any(k in cols_lower for k in ["amount", "txn amount", "net amount"])

            if has_date and has_desc and (has_debit_credit or has_amount):
                date_key = next(cols_lower[k] for k in ["date", "transaction date", "txn date", "value date"] if k in cols_lower)
                desc_key = next(cols_lower[k] for k in ["narration", "description", "particulars", "remarks"] if k in cols_lower)
                debit_key = next((cols_lower[k] for k in ["debit", "withdrawal", "withdrawal amt."] if k in cols_lower), None)
                credit_key = next((cols_lower[k] for k in ["credit", "deposit", "deposit amt."] if k in cols_lower), None)
                amount_key = next((cols_lower[k] for k in ["amount", "txn amount", "net amount"] if k in cols_lower), None)
                balance_key = next((cols_lower[k] for k in ["balance", "closing balance", "running balance"] if k in cols_lower), None)

                adapter = BankAdapterConfig(
                    bank_id="generic_standard",
                    bank_name="Standard Bank Statement",
                    date_column=date_key,
                    description_column=desc_key,
                    debit_column=debit_key,
                    credit_column=credit_key,
                    amount_column=amount_key,
                    balance_column=balance_key,
                    sign_convention=SignConvention.SEPARATE_COLUMNS if (debit_key and credit_key) else SignConvention.SIGNED_AMOUNT,
                    header_signatures=[],
                    header_row_identifier=date_key,
                )
            else:
                result.parse_confidence = 0.0
                result.needs_review = True
                result.warnings.append("Could not identify bank CSV format (no matching adapter).")
                result.raw_metadata = {"available_columns": available_cols}
                return result

        lines = content.splitlines()
        header_idx = self._locate_header_row(lines, adapter)
        csv_data = "\n".join(lines[header_idx:])

        try:
            df = pd.read_csv(io.StringIO(csv_data), skipinitialspace=True, on_bad_lines="skip")
        except Exception as exc:
            result.warnings.append(f"Failed to parse CSV with pandas: {exc}")
            result.parse_confidence = 0.0
            result.needs_review = True
            return result

        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]

        # Locate columns in df (case-insensitive fallback)
        col_lookup = {c.lower(): c for c in df.columns}

        def get_col_name(target: Optional[str], fallbacks: Optional[List[str]] = None) -> Optional[str]:
            if not target:
                return None
            targets = [target] + (fallbacks or [])
            for t in targets:
                if t in df.columns:
                    return t
                if t.lower() in col_lookup:
                    return col_lookup[t.lower()]
            return None

        date_col = get_col_name(adapter.date_column, ["Date", "Transaction Date", "Txn Date", "Value Date"])
        desc_col = get_col_name(adapter.description_column, ["Narration", "Description", "Transaction Remarks", "Transaction Description", "Particulars"])
        ref_col = get_col_name(adapter.reference_column, ["Chq./Ref.No.", "Cheque Number", "Reference Number", "Ref No./Cheque No.", "Ref / Chq No"])
        bal_col = get_col_name(adapter.balance_column, ["Closing Balance", "Balance (INR )", "Balance", "Running Balance"])
        debit_col = get_col_name(adapter.debit_column, ["Withdrawal Amt.", "Withdrawal Amount (INR )", "Debit", "Withdrawal"])
        credit_col = get_col_name(adapter.credit_column, ["Deposit Amt.", "Deposit Amount (INR )", "Credit", "Deposit"])
        amt_col = get_col_name(adapter.amount_column, ["Amount", "Net Amount", "Txn Amount"])
        type_col = get_col_name(adapter.type_column, ["Dr / Cr", "Dr/Cr", "Transaction Type", "Type", "CR/DR"])

        if not date_col:
            result.warnings.append(f"Configured date column '{adapter.date_column}' missing in CSV.")
            result.parse_confidence = 0.0
            result.needs_review = True
            return result

        date_formats = [adapter.date_format] + adapter.alternative_date_formats
        rows: List[ParsedTransactionRow] = []

        for _, raw_row in df.iterrows():
            date_raw = raw_row.get(date_col)
            txn_date = None
            for fmt in date_formats:
                try:
                    s = str(date_raw).strip()
                    if s and s.lower() not in ("nan", "none"):
                        txn_date = pd.to_datetime(s, format=fmt).date()
                        break
                except Exception:
                    continue
            used_fallback_date = False
            if not txn_date:
                txn_date = parse_date(date_raw)
                used_fallback_date = True

            if not txn_date:
                continue

            desc_raw = str(raw_row.get(desc_col, "")).strip() if desc_col else ""
            if not desc_raw or desc_raw.lower() in ("nan", "none"):
                desc_raw = "Unknown Narration"

            ref_no = None
            if ref_col:
                val = str(raw_row.get(ref_col, "")).strip()
                if val and val.lower() not in ("nan", "none", "-", ""):
                    ref_no = val

            amount = 0.0
            txn_type = "debit"
            confidence = 0.98
            if used_fallback_date:
                confidence -= 0.06
            if desc_raw == "Unknown Narration":
                confidence -= 0.10

            # Resolve amount and type based on adapter sign convention
            if adapter.sign_convention == SignConvention.SEPARATE_COLUMNS:
                debit_val = parse_numeric(raw_row.get(debit_col)) if debit_col else None
                credit_val = parse_numeric(raw_row.get(credit_col)) if credit_col else None

                if debit_val is not None and debit_val > 0:
                    amount = debit_val
                    txn_type = "debit"
                elif credit_val is not None and credit_val > 0:
                    amount = credit_val
                    txn_type = "credit"
            elif adapter.sign_convention == SignConvention.SIGNED_AMOUNT:
                amt_val = parse_numeric(raw_row.get(amt_col)) if amt_col else None
                if amt_val is not None and amt_val != 0:
                    amount = abs(amt_val)
                    if amt_val > 0:
                        txn_type = "credit" if adapter.positive_is_credit else "debit"
                    else:
                        txn_type = "debit" if adapter.positive_is_credit else "credit"
            elif adapter.sign_convention == SignConvention.TYPE_INDICATOR:
                amt_val = parse_numeric(raw_row.get(amt_col)) if amt_col else None
                raw_type = str(raw_row.get(type_col, "")).strip().lower() if type_col else ""
                resolved_type = adapter.type_mapping.get(raw_type)

                if amt_val is not None and amt_val > 0:
                    amount = amt_val
                    txn_type = resolved_type if resolved_type in ("credit", "debit") else "debit"

            if amount <= 0:
                continue

            bal_val = parse_numeric(raw_row.get(bal_col)) if bal_col else None
            if bal_val is None:
                confidence -= 0.04
            confidence = round(max(0.10, min(1.0, confidence)), 2)

            rows.append(
                ParsedTransactionRow(
                    date=txn_date,
                    description=desc_raw,
                    amount=round(amount, 2),
                    transaction_type=txn_type,
                    balance=round(bal_val, 2) if bal_val is not None else None,
                    reference_number=ref_no,
                    parse_confidence=confidence,
                    raw_row=dict(raw_row.dropna()) if hasattr(raw_row, "dropna") else None,
                )
            )

        # Disambiguate transaction direction using running balance deltas when balance is tracked
        for i in range(1, len(rows)):
            prev_b = rows[i - 1].balance
            curr_b = rows[i].balance
            if prev_b is not None and curr_b is not None:
                delta = round(curr_b - prev_b, 2)
                if abs(delta + rows[i].amount) <= 0.05:
                    rows[i].transaction_type = "debit"
                elif abs(delta - rows[i].amount) <= 0.05:
                    rows[i].transaction_type = "credit"

        result.rows = rows
        return reconcile_statement_balance(result)
