"""Logic-only transcription of the reviewed function; not a full repository module.
Source: monitoring_protocol_rules.py, pinned 872a4514, tool turn274file0.
Imports, annotations and comments are presentation-only; decision logic is retained.
"""
from typing import Any, Mapping


def expression_requires_diagnostic_coverage(preconditions, trigger_expression, exclusions):
    def _walk(node):
        if isinstance(node, Mapping):
            for key, operand in node.items():
                if str(key) in {"changed", "no_corresponding_record"}:
                    return True
                if _walk(operand):
                    return True
        elif isinstance(node, (list, tuple)):
            return any(_walk(item) for item in node)
        return False
    return any(_walk(tree) for tree in (preconditions, trigger_expression, exclusions))
