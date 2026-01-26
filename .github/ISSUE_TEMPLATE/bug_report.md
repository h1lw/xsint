name: Bug Report
description: Report a bug or unexpected behavior in KISS
title: "[BUG] "
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        ## Bug Description
        
        Provide a clear and concise description of the bug.
        
        ## Steps to Reproduce
        
        1. Go to '...'
        2. Click on '....'
        3. Scroll down to '....'
        4. See error
        
        ## Expected Behavior
        
        A clear and concise description of what you expected to happen.
        
        ## Actual Behavior
        
        A clear and concise description of what actually happened.
        
        ## Environment
        
        - OS: [e.g., macOS, Windows, Linux]
        - Python Version: [e.g., 3.8, 3.9, 3.10]
        - KISS Version: [e.g., v2.0.0, v2.1.0]
        - Installation Method: [e.g., pip, git clone]
        
        ## Additional Context
        
        Add any other context about the problem here.
        
        ## Configuration
        
        If applicable, provide your configuration (remove sensitive data):
        
        ```json
        {
          "api_keys": {
            "HIBP": "***",
            "IPINFO": "***"
          }
        }
        ```
        
        ## Logs
        
        If applicable, provide relevant logs (remove sensitive data):
        
        ```
        [Paste logs here]
        ```
  - type: textarea
    id: reproduction
    attributes:
      label: "Steps to Reproduce"
      description: "Detailed steps to reproduce the bug"
      placeholder: |
        1.
        2.
        3.
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: "Expected Behavior"
      description: "What you expected to happen"
    validations:
      required: true
  - type: textarea
    id: actual
    attributes:
      label: "Actual Behavior"
      description: "What actually happened"
    validations:
      required: true
  - type: dropdown
    id: os
    attributes:
      label: "Operating System"
      options:
        - macOS
        - Windows
        - Linux
        - Other
    validations:
      required: true
  - type: dropdown
    id: python_version
    attributes:
      label: "Python Version"
      options:
        - Python 3.8
        - Python 3.9
        - Python 3.10
        - Python 3.11
        - Python 3.12
        - Other
    validations:
      required: true
  - type: input
    id: kiss_version
    attributes:
      label: "KISS Version"
      description: "Version of KISS you are using"
      placeholder: "e.g., v2.0.0"
    validations:
      required: true
  - type: textarea
    id: additional_context
    attributes:
      label: "Additional Context"
      description: "Any other information about the bug"