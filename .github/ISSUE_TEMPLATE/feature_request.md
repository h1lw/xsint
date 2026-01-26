name: Feature Request
description: Suggest a new feature or enhancement for KISS
title: "[FEATURE] "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        ## Feature Description
        
        Provide a clear and concise description of the feature you would like to see.
        
        ## Problem Statement
        
        What problem does this feature solve? What limitation does it address?
        
        ## Proposed Solution
        
        Describe your solution in detail. How would this feature work?
        
        ## Use Cases
        
        Provide specific use cases for this feature:
        
        ### Use Case 1
        **User:** [Who would use this?]
        **Goal:** [What are they trying to accomplish?]
        **Benefit:** [How does this help them?]
        
        ### Use Case 2
        **User:** [Who would use this?]
        **Goal:** [What are they trying to accomplish?]
        **Benefit:** [How does this help them?]
        
        ## Alternatives Considered
        
        Describe any alternative solutions or features you've considered:
        
        - Alternative 1: [description]
        - Alternative 2: [description]
        
        ## Implementation Ideas
        
        If you have technical ideas for implementation, please describe them:
        
        - **Approach 1:** [description]
        - **Approach 2:** [description]
        
        ## Priority
        
        How important is this feature to you?
        
        - [ ] Critical - blocks my workflow
        - [ ] High - significant improvement
        - [ ] Medium - nice to have
        - [ ] Low - minor improvement
        
        ## Additional Context
        
        Add any other context, mockups, or examples about the feature request.
  - type: textarea
    id: description
    attributes:
      label: "Feature Description"
      description: "Clear and concise description of the feature"
      placeholder: "I would like to be able to..."
    validations:
      required: true
  - type: textarea
    id: problem
    attributes:
      label: "Problem Statement"
      description: "What problem does this feature solve?"
    validations:
      required: true
  - type: textarea
    id: solution
    attributes:
      label: "Proposed Solution"
      description: "Describe your solution in detail"
    validations:
      required: true
  - type: textarea
    id: use_cases
    attributes:
      label: "Use Cases"
      description: "Specific use cases for this feature"
      placeholder: |
        Use Case 1:
        User: 
        Goal: 
        Benefit: 
        
        Use Case 2:
        User: 
        Goal: 
        Benefit: 
    validations:
      required: false
  - type: textarea
    id: alternatives
    attributes:
      label: "Alternatives Considered"
      description: "Any alternative solutions or features you've considered"
    validations:
      required: false
  - type: dropdown
    id: priority
    attributes:
      label: "Priority"
      options:
        - Critical - blocks my workflow
        - High - significant improvement
        - Medium - nice to have
        - Low - minor improvement
    validations:
      required: true
  - type: textarea
    id: additional_info
    attributes:
      label: "Additional Context"
      description: "Any other context, mockups, or examples"
    validations:
      required: false