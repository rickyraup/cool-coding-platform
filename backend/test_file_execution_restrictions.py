#!/usr/bin/env python3
"""Test script to verify file execution restrictions are working."""

from app.websockets.handlers import validate_file_execution_command


def test_file_execution_restrictions():
    """Test the file execution validation function."""

    print("🧪 Testing file execution restrictions")
    print("=" * 50)

    # Test cases: (command, should_be_allowed, expected_filename)
    test_cases = [
        # Allowed commands
        ("python test.py", True, "test.py"),
        ("python3 script.py", True, "script.py"),
        ("node app.js", True, "app.js"),
        ("node server.ts", True, "server.ts"),
        ("python app.jsx", True, "app.jsx"),
        ("node component.tsx", True, "component.tsx"),
        ("python module.mjs", True, "module.mjs"),

        # Disallowed commands
        ("python test.txt", False, "test.txt"),
        ("node config.json", False, "config.json"),
        ("python readme.md", False, "readme.md"),
        ("./script.sh", False, "script.sh"),
        ("python data.csv", False, "data.csv"),
        ("node package.xml", False, "package.xml"),

        # Non-execution commands (should be allowed through)
        ("ls", False, ""),
        ("cat test.py", False, ""),
        ("mkdir folder", False, ""),
        ("rm test.txt", False, ""),
        ("echo hello", False, ""),
        ("pwd", False, ""),
    ]

    passed = 0
    total = len(test_cases)

    for command, should_be_allowed, expected_filename in test_cases:
        is_execution, filename, error_msg = validate_file_execution_command(command)

        # Determine if the command would be allowed (no error message)
        is_allowed = is_execution and not error_msg

        if is_execution:
            if should_be_allowed and is_allowed:
                print(f"✅ PASS: '{command}' -> allowed execution of {filename}")
                passed += 1
            elif not should_be_allowed and not is_allowed:
                print(f"✅ PASS: '{command}' -> blocked: {error_msg}")
                passed += 1
            else:
                if should_be_allowed:
                    print(f"❌ FAIL: '{command}' -> should be allowed but was blocked: {error_msg}")
                else:
                    print(f"❌ FAIL: '{command}' -> should be blocked but was allowed")
        else:
            # Non-execution command
            if not should_be_allowed:
                print(f"✅ PASS: '{command}' -> non-execution command (allowed)")
                passed += 1
            else:
                print(f"❌ FAIL: '{command}' -> expected to be execution command but wasn't detected")

    print("=" * 50)
    print(f"Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! File execution restrictions are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the validation logic.")
        return False


if __name__ == "__main__":
    test_file_execution_restrictions()