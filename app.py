from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from matcher import pick_complexes

DATA_PATH = Path(__file__).parent / "data" / "complexes.csv"

RU_LOCALE = {"number": {"decimal": ",", "thousands": " ", "grouping": [3], "currency": ["", ""]}}


def format_number(value):
    return f"{value:,.0f}".replace(",", " ")


def format_rub(value):
    if value >= 1000000:
        return f"{value / 1000000:.2f}".replace(".", ",") + " млн р"
    return format_number(value) + " р"


def render_card(row, budget):
    with st.container(border=True):
        st.subheader(row["name"])
        st.caption(f"{row['class'].capitalize()} | {row['developer']} | {row['district']}")
        st.metric("Примерная стоимость", format_rub(row["estimated_cost"]))
        if not row["fits_budget"]:
            over = format_rub(row["estimated_cost"] - budget)
            max_area = format_number(row["max_area"])
            st.warning(f"Дороже бюджета на {over}. На ваш бюджет хватит примерно на {max_area} м2.")
        st.write(f"Цена от: **{format_number(row['price_from_m2'])} р/м2**")
        st.write(f"Срок сдачи: **{row['completion']}**")
        st.markdown(f"[Источник]({row['source_url']})")


def render_picker(complexes):
    col1, col2, col3 = st.columns(3)
    city = col1.selectbox("Город", sorted(complexes["city"].unique()))
    budget_mln = col2.number_input("Бюджет, млн р", min_value=5.0, max_value=1000.0, value=40.0, step=0.5)
    area = col3.number_input("Площадь, м2", min_value=20, max_value=300, value=60, step=5)
    budget = budget_mln * 1000000

    picked = pick_complexes(complexes, city, budget, area)
    if not picked["fits_budget"].any():
        st.warning("В бюджет не укладывается ни один ЖК, показаны ближайшие по цене.")
    elif not picked["fits_budget"].all():
        st.info("В бюджет укладываются не все варианты, ближайшие подороже показаны с пометкой.")

    columns = st.columns(3)
    for i, row in picked.iterrows():
        with columns[i]:
            render_card(row, budget)

    st.caption("Стоимость = цена от за м2 * площадь. Реальная цена конкретной квартиры может быть выше.")


def render_data(complexes):
    st.subheader("Все ЖК")
    st.dataframe(
        complexes.style.format(format_number, subset=["price_from_m2"]),
        hide_index=True,
        height="content",
        column_config={
            "city": st.column_config.TextColumn("Город", width="medium"),
            "name": "ЖК",
            "developer": "Застройщик",
            "district": "Район",
            "class": "Класс",
            "price_from_m2": "Цена от, р/м2",
            "completion": "Срок сдачи",
            "source_url": st.column_config.LinkColumn("Источник", display_text="ссылка"),
        },
    )
    st.caption("Цены и сроки сверены с объявлениями ЦИАН 13.11.2026.")

    st.subheader("Цена от за м2")
    chart = alt.Chart(complexes).mark_bar().encode(
        x=alt.X("price_from_m2", title="Цена от, р/м2", axis=alt.Axis(tickCount=8)),
        y=alt.Y("name", title=None, sort="-x", axis=alt.Axis(labelLimit=300)),
        color=alt.Color("city", title="Город"),
        tooltip=[
            alt.Tooltip("name", title="ЖК"),
            alt.Tooltip("city", title="Город"),
            alt.Tooltip("price_from_m2", title="Цена от, р/м2", format=","),
        ],
    )
    st.altair_chart(chart.configure(locale=RU_LOCALE))

    st.subheader("По городам")
    summary = complexes.groupby("city")["price_from_m2"].agg(["min", "median"]).reset_index()
    st.dataframe(
        summary.style.format(format_number, subset=["min", "median"]),
        hide_index=True,
        column_config={"city": "Город", "min": "Минимум, р/м2", "median": "Медиана, р/м2"},
    )


st.set_page_config(page_title="Подбор ЖК", layout="wide")
st.title("Подбор ЖК по бюджету и площади")

complexes = pd.read_csv(DATA_PATH)

picker_tab, data_tab = st.tabs(["Подбор ЖК", "Данные"])
with picker_tab:
    render_picker(complexes)
with data_tab:
    render_data(complexes)
