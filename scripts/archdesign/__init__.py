"""archdesign: validate, render and assess cloud architecture specs.

Layers (dependencies point inward only):
    domain        pure entities and rules, stdlib only
    application   use cases and the ports they need
    adapters      JSON input, Mermaid/SVG output, Markdown reports
    cli           composition root that wires adapters into use cases
"""
