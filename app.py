import time
import pandas as pd
import streamlit as st

from core.aircraft import AircraftConfig
from core.passengers import make_demo_passengers, validate_passengers
from core.optimizer import optimize_seating, sequential_baseline, metrics
from visualization.cabin_3d import cabin_figure
from visualization.cabin_2d import seat_grid

st.set_page_config(page_title="AeroSeat AI", page_icon="✈️", layout="wide")

st.title("✈️ AeroSeat AI")
st.caption("Учебная система интеллектуальной рассадки пассажиров и анализа распределения массы")
st.warning(
    "Учебная модель. Геометрия салона и параметры массы/центровки условные; "
    "результаты не предназначены для реальной загрузки или эксплуатации самолёта."
)

config = AircraftConfig()
with st.sidebar:
    st.header("Настройки модели")
    n = st.slider("Количество пассажиров", 1, config.seat_count, 120)
    seed = st.number_input("Seed генерации", min_value=0, max_value=99999, value=7)
    st.markdown("---")
    st.markdown("**Учебная конфигурация**")
    st.write(f"Самолёт: {config.name}")
    st.write(f"Схема: {config.rows} рядов × 6 кресел")
    st.write(f"Вместимость модели: {config.seat_count}")
    st.caption("Это условная конфигурация 180 мест, а не точная схема конкретного борта.")

st.subheader("1. Данные пассажиров")
uploaded = st.file_uploader("Загрузить CSV (необязательно)", type=["csv"])
if uploaded is not None:
    try:
        passengers = validate_passengers(pd.read_csv(uploaded))
    except Exception as exc:
        st.error(f"Ошибка CSV: {exc}")
        st.stop()
else:
    passengers = validate_passengers(make_demo_passengers(n, int(seed)))

if len(passengers) > config.seat_count:
    st.error(f"Пассажиров ({len(passengers)}) больше доступных мест ({config.seat_count}).")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Пассажиров", len(passengers))
c2.metric("Групп", int((passengers["group_id"] != "").sum()))
c3.metric("Суммарная масса", f"{passengers.weight_kg.sum():,.1f} кг")
with st.expander("Посмотреть исходные данные"):
    st.dataframe(passengers, use_container_width=True, hide_index=True)

st.subheader("2. Оптимизация рассадки")
run = st.button("Запустить AeroSeat Optimizer", type="primary", use_container_width=True)
if "optimized" not in st.session_state:
    st.session_state.optimized = False
if run:
    result, elapsed = optimize_seating(passengers, config, int(seed))
    baseline = sequential_baseline(passengers, config)
    st.session_state.result = result
    st.session_state.baseline = baseline
    st.session_state.elapsed = elapsed
    st.session_state.optimized = True

if st.session_state.optimized:
    result = st.session_state.result
    baseline = st.session_state.baseline
    elapsed = st.session_state.elapsed
    opt_m = metrics(result)
    base_m = metrics(baseline)

    st.subheader("3. Результаты")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Назначено мест", f"{len(result)} / {config.seat_count}")
    m2.metric("Время оптимизации", f"{elapsed*1000:.2f} ms")
    m3.metric("Разброс массы зон", f"{opt_m['zone_mass_spread_kg']:.1f} кг",
              delta=f"{opt_m['zone_mass_spread_kg']-base_m['zone_mass_spread_kg']:.1f} кг vs baseline",
              delta_color="inverse")
    m4.metric("Учебная оценка CG", f"{opt_m['cg_m']:.3f} м")

    left, right = st.columns(2)
    with left:
        st.markdown("**Распределение массы по зонам**")
        chart = pd.DataFrame({
            "Зона": list(opt_m["zone_mass_kg"].keys()),
            "AeroSeat AI": list(opt_m["zone_mass_kg"].values()),
            "Baseline": list(base_m["zone_mass_kg"].values())
        }).set_index("Зона")
        st.bar_chart(chart)
    with right:
        st.markdown("**Сводка модели**")
        st.write(f"Общая условная масса модели: **{opt_m['total_mass_kg']:,.1f} кг**")
        st.write(f"Масса пассажиров: **{opt_m['passenger_mass_kg']:,.1f} кг**")
        st.write(f"Baseline CG: **{base_m['cg_m']:.3f} м**")
        st.write(f"AeroSeat CG: **{opt_m['cg_m']:.3f} м**")

    st.subheader("4. 3D-визуализация салона")
    st.plotly_chart(cabin_figure(result, config.rows), use_container_width=True)

    st.subheader("5. Карта кресел")
    grid = seat_grid(result, config.rows)
    st.dataframe(grid, use_container_width=True, height=420)

    st.subheader("6. Назначения пассажиров")
    st.dataframe(result[["passenger_id", "weight_kg", "group_id", "seat", "row", "zone", "arm_m"]],
                 use_container_width=True, hide_index=True)
    csv = result.to_csv(index=False).encode("utf-8")
    st.download_button("Скачать результат рассадки CSV", csv, "aeroseat_assignments.csv", "text/csv")
else:
    st.info("Нажмите «Запустить AeroSeat Optimizer», чтобы рассчитать рассадку и увидеть 3D-модель.")

with st.expander("Методология и ограничения"):
    st.markdown("""
    **Алгоритм:** группы сортируются по размеру, затем для каждой группы ищется непрерывный блок кресел
    в одном ряду и на одной стороне салона. Кандидаты оцениваются по мягким штрафам за предпочтения,
    места у прохода, загрузку продольной зоны и удаление от условного центра салона.

    **CG:** используется упрощённая формула `CG = total_moment / total_mass`.
    Параметры условной пустой массы, исходного момента и координат рядов — демонстрационные.
    Это не расчёт по Weight and Balance Manual конкретного самолёта.

    **Безопасность:** система не проверяет эксплуатационные ограничения, допустимый CG-envelope,
    фактические arms, багаж, топливо, экипаж, специальные места, аварийные выходы и сертификационные
    требования. Она предназначена только для обучения алгоритмам и визуализации.
    """)
