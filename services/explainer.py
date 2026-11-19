from models import Alert


NEXT_STEPS = {
    "critical": "Investigate immediately and take corrective action.",
    "warning": "Review the affected system and monitor the metric closely.",
    "info": "Review the metric and confirm whether any action is needed.",
}


def generate_explanation(alert: Alert) -> str:
    """Build a rule-based explanation from an alert's fields.

    The explanation compares the metric value with its threshold, selects a
    recommended next step based on severity, and includes the acknowledgement
    text.

    Args:
        alert: Alert whose severity, source, title, metric, value, and threshold
            are used to build the explanation.

    Returns:
        An explanation string, including "Not yet acknowledged" when the alert
        has no acknowledged-by value.

    Raises:
        KeyError: If the alert's severity has no configured recommended next
            step.
    """
    if alert.metric_value > alert.threshold:
        comparison = "exceeded"
    elif alert.metric_value < alert.threshold:
        comparison = "fell below"
    else:
        comparison = "reached"

    explanation = (
        f'This {alert.severity} alert from {alert.source} is titled "{alert.title}". '
        f"The {alert.metric_name} metric {comparison} its threshold: the current "
        f"value is {alert.metric_value}, compared with a threshold of "
        f"{alert.threshold}. Recommended next step: {NEXT_STEPS[alert.severity]}"
    )
    resolved_by = getattr(alert, "resolved_by", None) or "Not yet acknowledged"
    return explanation + f" Acknowledged by: {resolved_by}."
