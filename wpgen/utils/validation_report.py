"""Validation report formatting utilities."""

from typing import Any, Dict, List

from colorama import Fore, Style
from colorama import init as colorama_init

colorama_init(autoreset=True)


def print_validation_summary_table(results: Dict[str, Any], strict: bool = False) -> None:
    """Print a structured validation summary table.

    Args:
        results: Validation results dictionary
        strict: Whether strict mode was enabled
    """
    print("\n" + "="*80)
    print(f"{'Validation Summary':<50} {'Status':<10} {'Count':<10}")
    print("="*80)

    # Files checked
    files_checked = results.get("files_checked", 0)
    print(f"{'PHP files checked':<50} {'INFO':<10} {files_checked:<10}")

    # Valid files
    valid_files = results.get("valid_files", 0)
    status_color = Fore.GREEN if valid_files == files_checked else Fore.YELLOW
    print(f"{status_color}{'Valid files':<50} {'OK':<10} {valid_files:<10}{Style.RESET_ALL}")

    # Invalid files
    invalid_files = results.get("files_with_errors", results.get("invalid_files", 0))
    if invalid_files > 0:
        print(f"{Fore.RED}{'Invalid files':<50} {'ERROR':<10} {invalid_files:<10}{Style.RESET_ALL}")

    # Warnings
    warnings = results.get("warnings", [])
    warning_count = len(warnings)
    if warning_count > 0:
        color = Fore.RED if strict else Fore.YELLOW
        status = "ERROR" if strict else "WARNING"
        print(
            f"{color}{'Files with warnings':<50} {status:<10} "
            f"{warning_count:<10}{Style.RESET_ALL}"
        )

    # Errors
    errors = results.get("errors", [])
    error_count = len(errors)
    if error_count > 0:
        print(f"{Fore.RED}{'Total errors':<50} {'ERROR':<10} {error_count:<10}{Style.RESET_ALL}")

    print("="*80)

    # Overall status
    is_valid = results.get("valid", True)
    if is_valid and error_count == 0 and (not strict or warning_count == 0):
        print(f"\n{Fore.GREEN}✓ Validation PASSED{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}✗ Validation FAILED{Style.RESET_ALL}")
        if strict and warning_count > 0:
            print(f"{Fore.YELLOW}  Strict mode: Warnings treated as errors{Style.RESET_ALL}")

    # Print detailed errors and warnings
    if error_count > 0:
        print(f"\n{Fore.RED}Errors:{Style.RESET_ALL}")
        for i, error in enumerate(errors[:10], 1):  # Limit to first 10
            print(f"  {i}. {error}")
        if error_count > 10:
            print(f"  ... and {error_count - 10} more errors")

    if warning_count > 0:
        color = Fore.RED if strict else Fore.YELLOW
        status = "Errors" if strict else "Warnings"
        print(f"\n{color}{status}:{Style.RESET_ALL}")
        for i, warning in enumerate(warnings[:10], 1):  # Limit to first 10
            print(f"  {i}. {warning}")
        if warning_count > 10:
            print(f"  ... and {warning_count - 10} more warnings")

    print()


def print_file_validation_table(file_results: List[Dict[str, Any]]) -> None:
    """Print a table of per-file validation results.

    Args:
        file_results: List of file validation result dictionaries
    """
    print("\n" + "="*80)
    print(f"{'File':<50} {'Status':<15} {'Issues':<15}")
    print("="*80)

    for result in file_results:
        file_name = result.get("file", "unknown")
        if len(file_name) > 47:
            file_name = "..." + file_name[-44:]

        is_valid = result.get("valid", True)
        error_count = len(result.get("errors", []))
        warning_count = len(result.get("warnings", []))

        if is_valid and error_count == 0 and warning_count == 0:
            status = f"{Fore.GREEN}✓ Valid{Style.RESET_ALL}"
            issues = "-"
        elif error_count > 0:
            status = f"{Fore.RED}✗ Invalid{Style.RESET_ALL}"
            issues = f"{error_count} error(s)"
        else:
            status = f"{Fore.YELLOW}⚠ Warning{Style.RESET_ALL}"
            issues = f"{warning_count} warning(s)"

        print(f"{file_name:<50} {status:<24} {issues:<15}")

    print("="*80 + "\n")
