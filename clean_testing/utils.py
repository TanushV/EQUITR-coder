"""
Simple utility functions for demonstration purposes.
"""


def is_even(n: int) -> bool:
    """Return True if n is even, else False."""
    return n % 2 == 0


def reverse_string(s: str) -> str:
    """Return the reverse of the input string s."""
    return s[::-1]


def main() -> None:
    """Run self-tests for is_even and reverse_string."""
    # Test is_even function
    test_cases_even = [(0, True), (1, False), (2, True), (-1, False), (-2, True)]
    for num, expected in test_cases_even:
        result = is_even(num)
        status = "PASS" if result == expected else "FAIL"
        print(f"is_even({num}) = {result} (expected {expected}) - {status}")
    
    # Test reverse_string function
    test_cases_reverse = [("hello", "olleh"), ("", ""), ("a", "a"), ("abc", "cba")]
    for text, expected in test_cases_reverse:
        result = reverse_string(text)
        status = "PASS" if result == expected else "FAIL"
        print(f"reverse_string('{text}') = '{result}' (expected '{expected}') - {status}")


if __name__ == "__main__":
    main()