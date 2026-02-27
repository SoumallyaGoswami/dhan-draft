"""Tax calculation services."""


def calculate_old_regime_tax(income: float, deductions_80c: float = 0, deductions_80d: float = 0, 
                              hra_exemption: float = 0, other_deductions: float = 0) -> dict:
    """Calculate tax under old regime with deductions."""
    total_deductions = (
        min(deductions_80c, 150000) + 
        min(deductions_80d, 25000) + 
        hra_exemption + 
        other_deductions + 
        50000  # Standard deduction
    )
    
    taxable_income = max(income - total_deductions, 0)
    
    # Calculate tax based on slabs
    tax = 0
    remaining = taxable_income
    
    if remaining > 1000000:
        tax += (remaining - 1000000) * 0.30
        remaining = 1000000
    if remaining > 500000:
        tax += (remaining - 500000) * 0.20
        remaining = 500000
    if remaining > 250000:
        tax += (remaining - 250000) * 0.05
    
    cess = tax * 0.04
    total_tax = tax + cess
    
    return {
        "taxable_income": round(max(income - total_deductions, 0)),
        "tax": round(tax),
        "cess": round(cess),
        "total": round(total_tax),
        "effective_rate": round((total_tax / income * 100), 2) if income > 0 else 0,
        "deductions": round(total_deductions)
    }


def calculate_new_regime_tax(income: float) -> dict:
    """Calculate tax under new regime (no deductions)."""
    standard_deduction = 75000
    taxable_income = max(income - standard_deduction, 0)
    
    # Calculate tax based on new slabs
    tax = 0
    remaining = taxable_income
    
    slabs = [
        (300000, 0),
        (300000, 0.05),
        (300000, 0.10),
        (300000, 0.15),
        (300000, 0.20),
        (float('inf'), 0.30)
    ]
    
    for slab_amount, rate in slabs:
        if remaining <= 0:
            break
        chunk = min(remaining, slab_amount)
        tax += chunk * rate
        remaining -= chunk
    
    # Rebate for income up to 12L
    if taxable_income <= 1200000:
        tax = 0
    
    cess = tax * 0.04
    total_tax = tax + cess
    
    return {
        "taxable_income": round(taxable_income),
        "tax": round(tax),
        "cess": round(cess),
        "total": round(total_tax),
        "effective_rate": round((total_tax / income * 100), 2) if income > 0 else 0,
        "deductions": standard_deduction
    }


def calculate_capital_gains_tax(buy_price: float, sell_price: float, quantity: int, 
                                 holding_months: int, asset_type: str = "equity") -> dict:
    """Calculate capital gains tax."""
    gain = (sell_price - buy_price) * quantity
    gain_pct = ((sell_price - buy_price) / buy_price * 100) if buy_price > 0 else 0
    
    if asset_type == "equity":
        if holding_months >= 12:  # LTCG
            taxable_gain = max(gain - 125000, 0)  # Rs.1.25L exemption
            tax = taxable_gain * 0.125  # 12.5% LTCG tax
            tax_type = "LTCG"
        else:  # STCG
            tax = max(gain, 0) * 0.20  # 20% STCG tax
            tax_type = "STCG"
    else:  # Non-equity
        if holding_months >= 24:  # LTCG
            tax = max(gain, 0) * 0.20  # 20% with indexation
            tax_type = "LTCG"
        else:  # STCG
            tax = max(gain, 0) * 0.30  # As per income tax slab
            tax_type = "STCG"
    
    net_gain = gain - max(tax, 0)
    
    return {
        "gain": round(gain),
        "gain_pct": round(gain_pct, 2),
        "tax_type": tax_type,
        "tax": round(max(tax, 0)),
        "net_gain": round(net_gain),
        "explanation": f"{tax_type} of Rs.{round(max(tax, 0)):,} on {asset_type} held {holding_months} months."
    }


def calculate_fd_tax(principal: float, rate: float, years: int, tax_bracket: float) -> dict:
    """Calculate FD tax impact."""
    interest_per_year = principal * rate / 100
    total_interest = interest_per_year * years
    tax_per_year = interest_per_year * tax_bracket / 100
    total_tax = tax_per_year * years
    post_tax_return = total_interest - total_tax
    effective_rate = (post_tax_return / (principal * years)) * 100 if years > 0 else 0
    
    return {
        "total_interest": round(total_interest),
        "tax_per_year": round(tax_per_year),
        "total_tax": round(total_tax),
        "post_tax_return": round(post_tax_return),
        "effective_rate": round(effective_rate, 2),
        "explanation": f"At {tax_bracket}% bracket, effective FD rate: {effective_rate:.2f}% (pre-tax: {rate}%)."
    }
