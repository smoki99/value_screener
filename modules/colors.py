"""
ANSI color codes and colorization helpers for terminal output.
"""


class Color:
    """ANSI escape codes for colored terminal output."""
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def colorize_peg(value: float | None, formatted_str: str) -> str:
    """Colorize PEG ratio value.
    
    Args:
        value: The PEG ratio value (lower is better)
        formatted_str: Pre-formatted string to colorize
        
    Returns:
        Colorized string with ANSI codes
    """
    if value is None:
        return formatted_str
    if value <= 1.0:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value <= 1.5:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_gm(value: float | None, formatted_str: str) -> str:
    """Colorize gross margin value.
    
    Args:
        value: Gross margin as decimal (higher is better)
        formatted_str: Pre-formatted string to colorize
        
    Returns:
        Colorized string with ANSI codes
    """
    if value is None:
        return formatted_str
    if value >= 0.50:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value >= 0.30:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_gpa(value: float | None, formatted_str: str) -> str:
    """Colorize GP/A (Gross Profit / Assets) value.
    
    Args:
        value: GP/A ratio as decimal (higher is better)
        formatted_str: Pre-formatted string to colorize
        
    Returns:
        Colorized string with ANSI codes
    """
    if value is None:
        return formatted_str
    if value >= 0.30:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value >= 0.15:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_roe(value: float | None, formatted_str: str) -> str:
    """Colorize ROE (Return on Equity) value.
    
    Args:
        value: ROE as decimal (higher is better)
        formatted_str: Pre-formatted string to colorize
        
    Returns:
        Colorized string with ANSI codes
    """
    if value is None:
        return formatted_str
    if value >= 0.20:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value >= 0.10:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_pb(value: float | None, formatted_str: str) -> str:
    """Colorize P/B (Price to Book) value.
    
    Args:
        value: P/B ratio (lower is better)
        formatted_str: Pre-formatted string to colorize
        
    Returns:
        Colorized string with ANSI codes
    """
    if value is None:
        return formatted_str
    if value <= 5.0:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value <= 15.0:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_decile(value: int | None, formatted_str: str) -> str:
    """Colorize decile ranking value.
    
    Args:
        value: Decile rank 1-10 (higher is better)
        formatted_str: Pre-formatted string to colorize
        
    Returns:
        Colorized string with ANSI codes
    """
    if value is None:
        return formatted_str
    if value >= 8:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value >= 4:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_nm_rank(value: int | None, formatted_str: str) -> str:
    """Colorize Novy-Marx rank value.
    
    Args:
        value: NM rank (higher is better)
        formatted_str: Pre-formatted string to colorize
        
    Returns:
        Colorized string with ANSI codes
    """
    if value is None:
        return formatted_str
    if value >= 16:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value >= 10:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def colorize_asset_growth(value: float | None, formatted_str: str) -> str:
    """Colorize asset growth value.
    
    Args:
        value: Asset growth rate as decimal (lower is better)
        formatted_str: Pre-formatted string to colorize
        
    Returns:
        Colorized string with ANSI codes
    """
    if value is None:
        return formatted_str
    if value <= 0.10:
        return f"{Color.GREEN}{formatted_str}{Color.RESET}"
    elif value <= 0.25:
        return f"{Color.YELLOW}{formatted_str}{Color.RESET}"
    else:
        return f"{Color.RED}{formatted_str}{Color.RESET}"


def peg_zone(value: float | None) -> str:
    """Get PEG zone indicator with emoji.
    
    Args:
        value: PEG ratio value
        
    Returns:
        Zone string with emoji (🟢GÜNSTIG, 🟡FAIR, 🔴TEUER)
    """
    if value is None:
        return ""
    if value <= 1.0:
        return "🟢GÜNSTIG"
    elif value <= 1.5:
        return "🟡FAIR"
    else:
        return "🔴TEUER"
