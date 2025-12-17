/**
 * Check if there is an error with the message.
 * @param error The error being checked.
 * @returns Return wether the message gives an error or not.
 */
export function isErrorWithMessage(error: unknown): error is { response?: { data?: { message?: string } } } {
  return typeof error === "object" && error !== null && "response" in error;
}

/**
 * Check if the user entered a valid password.
 * @param password The password entered by the user.
 * @returns Returns whether the password is valid or not.
 */
export function validPassword(password: string): boolean {
  // Password must be between 12 and 32 characters
  const lengthValid = password.length >= 12 && password.length <= 32;

  // Passwords include at least one numeric character [0, 9]
  const numberValid = /[0-9]/.test(password);

  // Password must include at least one special character [!@#$%^&*]
  const specialCharValid = /[!@#$%^&*]/.test(password);

  return lengthValid && numberValid && specialCharValid;
}
/**
 * Reset the input fields based on the dialog type.
 * @returns An empty string representing the reset username field.
 */
export function resetValue(): string {
  return "";
}

/**
 * Reset the username and password fields.
 * @returns A tuple containing the reset username and password fields.
 */
export function resetUsernameAndPassword(): [string, string] {
  return [resetValue(), resetValue()];
}

/**
 * Toggle password visibility.
 * @param IsPassword Indicates whether the password is currently visible.
 * @returns The updated password input type.
 */
export function toggleText(IsPassword: string): string {
  return IsPassword === "password" ? "text" : "password";
}
