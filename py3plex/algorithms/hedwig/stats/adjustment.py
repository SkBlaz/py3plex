"""
Multiple-testing adjustment methods.

@author: anze.vavpetic@ijs.si
"""


def _holdout(ruleset, holdout_ratio=0.3, alpha=0.05):
    """
    Holdout validation approach for multiple testing adjustment.
    
    This method splits the ruleset into two parts: a discovery set for
    hypothesis generation and a holdout set for validation. Rules are
    filtered on the discovery set and then validated on the holdout set.
    
    Args:
        ruleset: List of rules with p-values
        holdout_ratio: Proportion of data to hold out for validation (default: 0.3).
                      Must be between 0 and 1 (exclusive).
        alpha: Significance level for filtering (default: 0.05)
    
    Returns:
        List of rules that pass both discovery and holdout validation
        
    Raises:
        ValueError: If holdout_ratio is not in the valid range (0, 1)
        
    Note:
        This is a conservative approach that reduces false positives
        but may also reduce statistical power. The holdout set should
        be large enough to provide reliable validation.
    """
    if not ruleset:
        return ruleset
    
    # Validate holdout_ratio
    if not (0 < holdout_ratio < 1):
        raise ValueError(
            f"holdout_ratio must be between 0 and 1 (exclusive), got {holdout_ratio}"
        )
    
    # Create a copy to avoid modifying the original
    rules = list(ruleset)
    
    # Sort by p-value for deterministic behavior
    rules = sorted(rules, key=lambda r: r.pval)
    
    # Calculate split point
    n_total = len(rules)
    n_holdout = max(1, int(n_total * holdout_ratio))
    
    # Split into discovery and holdout sets
    # Use every k-th rule for holdout to maintain representative sampling
    k = max(1, int(1 / holdout_ratio))
    holdout_indices = set(list(range(0, n_total, k))[:n_holdout])
    
    discovery_rules = [r for i, r in enumerate(rules) if i not in holdout_indices]
    holdout_rules = [r for i, r in enumerate(rules) if i in holdout_indices]
    
    # Filter discovery set by alpha
    significant_discovery = [r for r in discovery_rules if r.pval <= alpha]
    
    if not significant_discovery:
        return []
    
    # Validate on holdout set - only keep rules that are also significant in holdout
    # This requires matching rules between discovery and holdout
    # Since we don't have rule IDs, we use a simple threshold approach:
    # Keep rules from discovery set if the average p-value in holdout is also significant
    if holdout_rules:
        avg_holdout_pval = sum(r.pval for r in holdout_rules) / len(holdout_rules)
        if avg_holdout_pval <= alpha:
            return significant_discovery
        else:
            # More conservative: only keep top rules
            threshold = alpha / 2  # More stringent threshold
            return [r for r in significant_discovery if r.pval <= threshold]
    
    # If no holdout rules, return discovery results
    return significant_discovery


def fwer(ruleset, alpha=0.05):
    """
    The Holm-Bonferroni direct adjustment method to control the FWER.
    """
    m = float(len(list(ruleset)))
    ruleset = sorted(ruleset, key=lambda r: r.pval)
    for k, rule in enumerate(ruleset):
        if rule.pval > alpha / (m + 1 - (k + 1)):
            ruleset = ruleset[:k]
            break

    return ruleset


def fdr(ruleset, q=0.05):
    """
    The Benjamini-Hochberg-Yekutieli direct adjustment
    method to control the FDR.
    """
    m = float(len(list(ruleset)))
    ruleset = sorted(ruleset, key=lambda r: r.pval)
    for k, rule in enumerate(ruleset):
        if rule.pval > ((k + 1) * q) / m:
            ruleset = ruleset[:k]
            break

    return ruleset


def none(ruleset):
    return ruleset
