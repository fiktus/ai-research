import pandas as pd


def pick_complexes(df, city, budget, area):
    options = df[df["city"] == city]
    options["estimated_cost"] = options["price_from_m2"] * area
    options["max_area"] = budget / options["price_from_m2"]
    options["fits_budget"] = options["estimated_cost"] <= budget

    # сначала самые дорогие из тех, что влезают в бюджет, потом ближайшие подороже
    fits = options[options["fits_budget"]].sort_values("estimated_cost", ascending=False)
    over = options[~options["fits_budget"]].sort_values("estimated_cost")
    return pd.concat([fits, over]).head(3).reset_index(drop=True)
