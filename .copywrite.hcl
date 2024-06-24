schema_version = 1

project {
  license        = "GPL-3.0-or-later"
  copyright_year = 2024
  copyright_holder = "Van Gogh Museum"

  # (OPTIONAL) A list of globs that should not have copyright/license headers.
  # Supports doublestar glob patterns for more flexibility in defining which
  # files or folders should be ignored
  header_ignore = [
    "venv/**",
    "documentation/**",
    "xrf_explorer/client/node_modules/**",
    "xrf_explorer/client/dist/**",
  ]
}
