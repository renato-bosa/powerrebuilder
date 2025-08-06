import functools
import json
import logging
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PowerBuilderDecoder:
    """PowerBuilder binary decoder with comprehensive corruption handling."""

    def __init__(self) -> None:
        """Initialize the decoder with comprehensive dictionaries and caches."""
        # Domain dictionary will be lazy loaded
        self._domain_dict_cache: set[str] | None = None

        # Load learned vocabulary if available
        self._load_learned_vocabulary()

        # Caches for performance
        self.corruption_fix_cache: dict[str, str] = {}

        # Pattern-specific fixes
        self.pattern_fixes = self._initialize_pattern_fixes()

        # SQL parameter patterns for v4 functionality
        self.parameter_patterns = self._initialize_parameter_patterns()
    
    @property
    def domain_dict(self) -> set[str]:
        """Get domain dictionary with lazy loading."""
        if self._domain_dict_cache is None:
            self._domain_dict_cache = self._initialize_domain_dictionary()
        return self._domain_dict_cache

        # Position analysis data
        self.position_stats: dict[int, Counter] = defaultdict(Counter)
        self.corruption_patterns: list[tuple[str, str]] = []

        # Configuration
        self.min_word_length = 3
        self.max_candidates = 50
        self.context_weight = 0.3

    @functools.lru_cache(maxsize=1)
    def _initialize_domain_dictionary(self) -> set[str]:
        """Initialize comprehensive domain dictionary from all implementations (lazy loaded)."""
        # Core PowerBuilder/SQL terms - lazy loaded to reduce memory on import
        terms = {
            # SQL Keywords
            "select",
            "from",
            "where",
            "insert",
            "update",
            "delete",
            "into",
            "values",
            "set",
            "join",
            "left",
            "right",
            "inner",
            "outer",
            "on",
            "and",
            "or",
            "not",
            "in",
            "exists",
            "between",
            "like",
            "order",
            "by",
            "group",
            "having",
            "union",
            "intersect",
            "except",
            "case",
            "when",
            "then",
            "else",
            "end",
            "as",
            "distinct",
            "all",
            "any",
            "some",
            "count",
            "sum",
            "avg",
            "min",
            "max",
            "coalesce",
            "nullif",
            "cast",
            "convert",
            "substring",
            "trim",
            "upper",
            "lower",
            "length",
            # PowerBuilder Keywords
            "if",
            "elseif",
            "for",
            "to",
            "step",
            "next",
            "while",
            "loop",
            "do",
            "until",
            "return",
            "continue",
            "break",
            "exit",
            "function",
            "subroutine",
            "event",
            "public",
            "private",
            "protected",
            "global",
            "shared",
            "constant",
            "readonly",
            "ref",
            "value",
            "reference",
            # PowerBuilder Types
            "integer",
            "long",
            "decimal",
            "real",
            "double",
            "boolean",
            "char",
            "string",
            "date",
            "time",
            "datetime",
            "blob",
            "powerobject",
            "nonvisualobject",
            "window",
            "userobject",
            "datawindow",
            "datastore",
            "structure",
            "menu",
            "application",
            # PowerBuilder Objects/Properties
            "this",
            "super",
            "parent",
            "control",
            "object",
            "width",
            "height",
            "x",
            "y",
            "visible",
            "enabled",
            "text",
            "tag",
            "name",
            "title",
            "backcolor",
            "textcolor",
            "font",
            "weight",
            "italic",
            "underline",
            # DataWindow-specific
            "retrieve",
            "insertrow",
            "deleterow",
            "getrow",
            "setrow",
            "rowcount",
            "getitemstring",
            "getitemnumber",
            "getitemdate",
            "setitem",
            "accepttext",
            "resetupdate",
            "setfilter",
            "filter",
            "setsort",
            "sort",
            "sharedata",
            "sharedataoff",
            "describe",
            "modify",
            "print",
            "saveas",
            # Common Methods
            "open",
            "close",
            "show",
            "hide",
            "move",
            "resize",
            "setfocus",
            "post",
            "trigger",
            "dynamic",
            "create",
            "destroy",
            "isnull",
            "setnull",
            "isvalid",
            "classname",
            "typeof",
            "messagebox",
            "beep",
            # Events
            "clicked",
            "doubleclicked",
            "rbuttondown",
            "constructor",
            "destructor",
            "activate",
            "deactivate",
            "key",
            "losefocus",
            "getfocus",
            "dragdrop",
            "dragenter",
            "dragleave",
            "dragwithin",
            # Common Prefixes
            "cb_",
            "cbx_",
            "ddlb_",
            "dw_",
            "em_",
            "gb_",
            "lb_",
            "mle_",
            "pb_",
            "rb_",
            "sle_",
            "st_",
            "tab_",
            "tv_",
            "uo_",
            "w_",
            "m_",
            "n_",
            "u_",
            "f_",
            "of_",
            "uf_",
            "gf_",
            # Common Suffixes
            "_ok",
            "_cancel",
            "_save",
            "_delete",
            "_new",
            "_edit",
            "_search",
            "_print",
            "_close",
            "_exit",
            "_apply",
            "_reset",
            "_refresh",
            "_update",
            "_add",
            "_remove",
            "_clear",
            "_copy",
            "_paste",
            "_cut",
            "_undo",
            "_redo",
            "_find",
            "_replace",
            "_first",
            "_last",
            "_next",
            "_prior",
            "_up",
            "_down",
            "_left",
            "_right",
            "_all",
            "_none",
            "_select",
            "_deselect",
            # Business Terms
            "customer",
            "product",
            "invoice",
            "payment",
            "account",
            "transaction",
            "employee",
            "department",
            "company",
            "address",
            "phone",
            "email",
            "status",
            "total",
            "quantity",
            "price",
            "discount",
            "tax",
            "shipping",
            "user",
            "password",
            "login",
            "logout",
            "session",
            "report",
            "document",
            "file",
            "folder",
            "database",
            "table",
            "column",
            "row",
            "field",
            "record",
            "index",
            "primary",
            "foreign",
            "unique",
            "constraint",
            "procedure",
            "view",
            # Common Patterns and Fragments
            "get_",
            "set_",
            "is_",
            "has_",
            "can_",
            "should_",
            "will_",
            "did_",
            "was_",
            "_id",
            "_no",
            "_num",
            "_code",
            "_name",
            "_desc",
            "_date",
            "_time",
            "_amt",
            "_amount",
            "_qty",
            "_quantity",
            "_flag",
            "_ind",
            "_indicator",
            # Additional Terms
            "search",
            "export",
            "import",
            "preview",
            "save",
            "load",
            "new",
            "edit",
            "cancel",
            "ok",
            "yes",
            "no",
            "true",
            "false",
            "active",
            "inactive",
            "pending",
            "approved",
            "rejected",
            "completed",
            "processing",
            "error",
            "warning",
            "info",
            "success",
            "failure",
            "exception",
            "trace",
            "debug",
            "log",
        }

        # Add variations (uppercase, title case)
        variations = set()
        for term in terms:
            variations.add(term)
            variations.add(term.upper())
            variations.add(term.title())

        return variations

    def _load_learned_vocabulary(self) -> None:
        """Load learned vocabulary from JSON file if available."""
        learned_vocab_path = (
            Path(__file__).parent.parent.parent.parent
            / "reference"
            / "learned_vocabulary.json"
        )
        if learned_vocab_path.exists():
            try:
                with Path(learned_vocab_path).open() as f:
                    learned_data = json.load(f)
                    self.domain_dict.update(learned_data.get("words", []))
                    logger.info(
                        f"Loaded {len(learned_data.get('words', []))} learned words"
                    )
            except Exception as e:
                logger.warning("Failed to load learned vocabulary: %s", e)

    def _initialize_pattern_fixes(self) -> list[tuple[re.Pattern, str | Any]]:
        """Initialize regex-based pattern fixes for common corruptions."""
        return [
            # Fix corrupted operators
            (re.compile(r"\.Ā\s"), "."),
            (re.compile(r"([a-zA-Z])\s+Ā\s+([a-zA-Z])"), r"\1.\2"),
            (re.compile(r"([0-9])\s+Ā\s+([0-9])"), r"\1.\2"),
            # Fix corrupted assignments
            (re.compile(r"\s+Ā\s+="), " ="),
            (re.compile(r"=\s+Ā\s+"), "= "),
            # Fix SQL-specific patterns
            (re.compile(r"\bWHERE\s+Ā\s+"), "WHERE "),
            (re.compile(r"\bAND\s+Ā\s+"), "AND "),
            (re.compile(r"\bOR\s+Ā\s+"), "OR "),
            # Common PowerBuilder patterns
            (re.compile(r"\.TriggerĀEvent"), ".TriggerEvent"),
            (re.compile(r"Ā_detail"), "_detail"),
            (re.compile(r"Ā_list"), "_list"),
            # Handle parameter placeholders
            (re.compile(r"VALUES\s*\([^)]*Ā[^)]*\)"), self._fix_values_clause),
        ]

    def _initialize_parameter_patterns(self) -> list[re.Pattern]:
        """Initialize patterns for SQL parameter detection."""
        return [
            re.compile(r":\w+"),  # :parameter
            re.compile(r"\?\d*"),  # ? or ?1, ?2
            re.compile(r"@\w+"),  # @parameter
            re.compile(r"\$\d+"),  # $1, $2
        ]

    def _fix_values_clause(self, match: re.Match) -> str:
        """Fix corrupted VALUES clause in SQL."""
        values_str = match.group(0)
        # Replace Ā with comma in VALUES clause
        return re.sub(r"\s*Ā\s*", ", ", values_str)

    def decode_text(self, data: bytes, context: str = "") -> str:
        """Main decoding method with comprehensive corruption handling."""
        # Try standard encodings first
        for encoding in ["utf-8", "cp1252", "latin-1"]:
            try:
                text = data.decode(encoding)
                if self._is_valid_text(text):
                    return self._post_process_text(text, context)
            except UnicodeDecodeError:
                continue

        # Fallback to character-by-character decoding
        return self._decode_with_recovery(data, context)

    def _is_valid_text(self, text: str) -> bool:
        """Check if decoded text is valid."""
        if not text or len(text.strip()) == 0:
            return False

        # Check for too many special characters
        special_chars = sum(1 for c in text if ord(c) > 127)
        if special_chars > len(text) * 0.3:  # More than 30% special chars
            return False

        return True

    def _decode_with_recovery(self, data: bytes, context: str) -> str:
        """Decode with character-by-character recovery."""
        chars = []
        i = 0

        while i < len(data):
            # Try multi-byte sequences
            decoded = False
            for length in [4, 3, 2, 1]:
                if i + length <= len(data):
                    try:
                        char = data[i : i + length].decode("utf-8")
                        chars.append(char)
                        i += length
                        decoded = True
                        break
                    except UnicodeDecodeError:
                        continue

            if not decoded:
                # Single byte fallback
                byte = data[i]
                if 32 <= byte <= 126:  # Printable ASCII
                    chars.append(chr(byte))
                else:
                    # Use placeholder for non-printable
                    chars.append("�")
                i += 1

        text = "".join(chars)
        return self._post_process_text(text, context)

    def _post_process_text(self, text: str, context: str) -> str:
        """Apply post-processing fixes to decoded text."""
        # Apply pattern fixes
        for pattern, replacement in self.pattern_fixes:
            if callable(replacement):
                text = pattern.sub(replacement, text)
            else:
                text = pattern.sub(replacement, text)

        # Fix common corruptions
        text = self._fix_common_corruptions(text, context)

        # Clean up whitespace
        return " ".join(text.split())

    def _fix_common_corruptions(self, text: str, context: str) -> str:
        """Fix common corruption patterns."""
        # Check cache first
        cache_key = f"{text[:50]}:{context}"
        if cache_key in self.corruption_fix_cache:
            return self.corruption_fix_cache[cache_key]

        fixed_text = text

        # Fix corrupted words
        words = fixed_text.split()
        fixed_words = []

        for word in words:
            if self._is_corrupted(word):
                fixed_word = self._fix_corrupted_word(word, context)
                fixed_words.append(fixed_word)
            else:
                fixed_words.append(word)

        fixed_text = " ".join(fixed_words)

        # Cache the result
        self.corruption_fix_cache[cache_key] = fixed_text

        return fixed_text

    def _is_corrupted(self, word: str) -> bool:
        """Check if a word appears to be corrupted."""
        # Contains special characters
        if any(ord(c) > 127 for c in word):
            return True

        # Unusual character combinations
        if re.search(r"[A-Z]{3,}[a-z]+[A-Z]+", word):  # Mixed case pattern
            return True

        # Not in dictionary and looks suspicious
        if word.lower() not in self.domain_dict and len(word) > 3:
            # Check for common corruption patterns
            if re.search(r"Ā|ă|Ă|ā", word):
                return True

        return False

    def _fix_corrupted_word(self, word: str, context: str) -> str:
        """Fix a corrupted word using various strategies."""
        # Remove obvious corruption characters
        cleaned = re.sub(r"[Āăāþÿ]", "", word)

        # If cleaned word is in dictionary, use it
        if cleaned.lower() in self.domain_dict:
            return cleaned

        # Try to find best match in dictionary
        best_match = self._find_best_match(cleaned, context)
        if best_match:
            return best_match

        # Return cleaned version as fallback
        return cleaned if cleaned else word

    def _find_best_match(self, word: str, context: str) -> str | None:
        """Find best dictionary match for a word."""
        word_lower = word.lower()

        # Exact match
        if word_lower in self.domain_dict:
            return word

        # Prefix match
        matches = [term for term in self.domain_dict if term.startswith(word_lower[:3])]

        if matches:
            # Score matches based on similarity and context
            scored_matches = []
            for match in matches:
                score = self._calculate_similarity(word_lower, match.lower())
                if context:
                    # Boost score if match appears in context
                    if match in context.lower():
                        score += self.context_weight

                scored_matches.append((match, score))

            # Return best match
            scored_matches.sort(key=lambda x: x[1], reverse=True)
            if scored_matches and scored_matches[0][1] > 0.6:
                return scored_matches[0][0]

        return None

    def _calculate_similarity(self, word1: str, word2: str) -> float:
        """Calculate similarity between two words."""
        # Simple character-based similarity
        if not word1 or not word2:
            return 0.0

        # Length similarity
        len_sim = 1.0 - abs(len(word1) - len(word2)) / max(len(word1), len(word2))

        # Character overlap
        common_chars = sum(1 for c in word1 if c in word2)
        char_sim = common_chars / max(len(word1), len(word2))

        # Prefix similarity
        prefix_len = 0
        for i in range(min(len(word1), len(word2))):
            if word1[i] == word2[i]:
                prefix_len += 1
            else:
                break
        prefix_sim = prefix_len / max(len(word1), len(word2))

        # Weighted average
        return len_sim * 0.2 + char_sim * 0.3 + prefix_sim * 0.5


class MagicNumbers:
    """Magic numbers used in PowerBuilder file extraction."""

    # DataWindow markers
    DATAWINDOW_HEADER = b"dw"
    DW_HEADER_SIGNATURE = b"datawindow("
    RELEASE_SIGNATURE = b"release"

    # PBD/Object markers
    OBJECT_DESCRIPTOR = b"OBJ"
    PBD_HEADER = b"HDR*"

    # General markers
    BINARY_MARKER = b"\x00\x00"
    SQL_MARKER = b"SQL"
    RELEASE_MARKER = b"release"

    # DataWindow binary markers (from history)
    GRID_MARKER = b"\x01\x02\x03"
    TABULAR_MARKER = b"\x02\x03\x04"

    # Numeric markers
    BINARY_MARKER_NUM = 0x90
    TEXT_MARKER = 0x00

    # Corrupt size indicators
    CORRUPT_SIZES = {0, 0xFFFFFFFF, 0xDEADBEEF}


# Export the decoder class
__all__ = ["MagicNumbers", "PowerBuilderDecoder"]
