name: Pull Request Template
description: Template for pull requests to KISS
title: ""
labels: []
body:
  - type: markdown
    attributes:
      value: |
        ## Description
        
        Provide a clear description of changes made in this pull request.
        
        ## Type of Change
        
        - [ ] Bug fix (non-breaking change that fixes an issue)
        - [ ] New feature (non-breaking change that adds functionality)
        - [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
        - [ ] Documentation update
        - [ ] Refactoring (code cleanup without functional changes)
        - [ ] Performance improvement
        - [ ] Other (please describe)
        
        ## Testing
        
        ### How Tested
        
        - [ ] Unit tests pass
        - [ ] Integration tests pass
        - [ ] Manual testing completed
        - [ ] Tested with real API keys (if applicable)
        - [ ] Performance testing completed (if applicable)
        
        ### Test Environment
        
        - **OS:** [e.g., macOS 13.0, Ubuntu 22.04, Windows 11]
        - **Python Version:** [e.g., 3.9, 3.10, 3.11]
        - **Dependencies:** [List any specific dependency versions used]
        
        ## Checklist
        
        ### Code Quality
        
        - [ ] Code follows project style guidelines
        - [ ] Self-review of the code completed
        - [ ] Documentation added/updated as needed
        - [ ] Type hints added where appropriate
        - [ ] Error handling implemented appropriately
        
        ### Testing
        
        - [ ] New tests added for new functionality
        - [ ] Existing tests still pass
        - [ ] Edge cases tested
        - [ ] Performance impact considered
        
        ### Security
        
        - [ ] No hardcoded credentials or sensitive data
        - [ ] Input validation implemented
        - [ ] Rate limiting considered
        - [ ] Error messages don't leak sensitive information
        
        ### Documentation
        
        - [ ] README updated if needed
        - [ ] API documentation updated if needed
        - [ ] Plugin development guide updated if applicable
        - [ ] Changelog updated
        - [ ] Examples updated if applicable
        
        ## API Changes (if applicable)
        
        ### Breaking Changes
        
        - [ ] None
        - [ ] [List breaking changes]
        
        ### New Features
        
        - [ ] None
        - [ ] [List new features]
        
        ### Deprecations
        
        - [ ] None
        - [ ] [List deprecated features]
        
        ## Performance Impact
        
        - [ ] No performance impact
        - [ ] Minor performance improvement
        - [ ] Significant performance improvement
        - [ ] Performance regression (please explain)
        
        ## Additional Context
        
        Add any other context about the pull request here.
        
        ## Screenshots (if applicable)
        
        Add screenshots to help explain your changes:
        
        ## Related Issues
        
        Link to any related issues:
        
        - Closes #[issue_number]
        - Related to #[issue_number]
        
        ## Review Focus
        
        Areas where you would like reviewers to focus:
        
        - [ ] General code review
        - [ ] Security review
        - [ ] Performance review
        - [ ] Documentation review
        - [ ] Plugin architecture review
        - [ ] Async implementation review
  - type: textarea
    id: description
    attributes:
      label: "Description"
      description: "Clear description of changes made"
      placeholder: "This PR adds..."
    validations:
      required: true
  - type: textarea
    id: test_details
    attributes:
      label: "Testing Details"
      description: "How you tested these changes"
      placeholder: "I tested by running..."
    validations:
      required: true
  - type: dropdown
    id: change_type
    attributes:
      label: "Primary Change Type"
      options:
        - Bug fix
        - New feature
        - Breaking change
        - Documentation update
        - Refactoring
        - Performance improvement
        - Other
    validations:
      required: true
  - type: checkboxes
    id: checklists
    attributes:
      label: "Quality Checklist"
      description: "Please complete all applicable items"
      options:
        - label: "Code follows project style guidelines"
          required: false
        - label: "Self-review completed"
          required: false
        - label: "Documentation updated"
          required: false
        - label: "Tests added/updated"
          required: false
        - label: "No hardcoded credentials"
          required: false
        - label: "Input validation implemented"
          required: false
        - label: "Changelog updated"
          required: false
  - type: textarea
    id: api_changes
    attributes:
      label: "API Changes"
      description: "Describe any API changes"
      placeholder: "Breaking changes, new features, deprecations..."
    validations:
      required: false
  - type: textarea
    id: performance
    attributes:
      label: "Performance Impact"
      description: "Describe performance impact"
      placeholder: "No impact / improvement / regression"
    validations:
      required: false
  - type: textarea
    id: related_issues
    attributes:
      label: "Related Issues"
      description: "Link to related GitHub issues"
      placeholder: "Closes #123, Related to #456"
    validations:
      required: false