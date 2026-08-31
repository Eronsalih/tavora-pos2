SUBSCRIPTION_PLANS = {
    # =====================================================
    # STARTER
    # =====================================================
    "starter_monthly": {
        "name": "Starter",
        "tier": "starter",
        "billing_period": "monthly",
        "duration_days": 30,
        "prices": {
            "EUR": 2490,      # 24.90 EUR
            "ALL": 249000,    # 2,490.00 ALL
        },
    },
    "starter_yearly": {
        "name": "Starter",
        "tier": "starter",
        "billing_period": "yearly",
        "duration_days": 365,
        "prices": {
            "EUR": 24900,      # 249.00 EUR
            "ALL": 2490000,    # 24,900.00 ALL
        },
    },

    # =====================================================
    # PRO
    # =====================================================
    "pro_monthly": {
        "name": "Pro",
        "tier": "pro",
        "billing_period": "monthly",
        "duration_days": 30,
        "prices": {
            "EUR": 3990,      # 39.90 EUR
            "ALL": 399000,    # 3,990.00 ALL
        },
    },
    "pro_yearly": {
        "name": "Pro",
        "tier": "pro",
        "billing_period": "yearly",
        "duration_days": 365,
        "prices": {
            "EUR": 39900,      # 399.00 EUR
            "ALL": 3990000,    # 39,900.00 ALL
        },
    },

    # =====================================================
    # BUSINESS
    # =====================================================
    "business_monthly": {
        "name": "Business",
        "tier": "business",
        "billing_period": "monthly",
        "duration_days": 30,
        "prices": {
            "EUR": 5990,      # 59.90 EUR
            "ALL": 599000,    # 5,990.00 ALL
        },
    },
    "business_yearly": {
        "name": "Business",
        "tier": "business",
        "billing_period": "yearly",
        "duration_days": 365,
        "prices": {
            "EUR": 59900,      # 599.00 EUR
            "ALL": 5990000,    # 59,900.00 ALL
        },
    },

    # =====================================================
    # LEGACY
    # =====================================================
    #
    # E mbajmë për bizneset/testet e vjetra që aktualisht
    # kanë subscription_plan = "pro".
    #
    # Pagesat e reja nuk duhet ta përdorin këtë key.
    #
    "pro": {
        "name": "Pro",
        "tier": "pro",
        "billing_period": "monthly",
        "duration_days": 30,
        "prices": {
            "EUR": 3990,
            "ALL": 399000,
        },
    },
}