import altair as alt
import streamlit as st

from src.database.database_setup import DatabaseSetup
from src.recommendations.collaborative_filtering import ProductRecommender


st.set_page_config(page_title="Neo4j Recommendation Demo", layout="wide")


CHART_COLORS = {
    "graph": "#1f77b4",
    "category": "#ff7f0e",
    "user_reco": "#2ca02c",
    "category_reco": "#d62728",
}


def apply_dashboard_theme():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(31, 119, 180, 0.12), transparent 28%),
                radial-gradient(circle at top right, rgba(255, 127, 14, 0.10), transparent 24%),
                linear-gradient(180deg, #f7f9fc 0%, #eef3f9 100%);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        }
        .section-card {
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 20px;
            padding: 1rem 1.1rem 0.8rem 1.1rem;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
            margin-bottom: 1rem;
        }
        .section-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #162033;
            margin-bottom: 0.3rem;
        }
        .section-copy {
            font-size: 0.92rem;
            color: #52607a;
            margin-bottom: 0.75rem;
        }
        div[data-testid="stDataFrame"] {
            border-radius: 16px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def open_card(title, copy=None):
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if copy:
        st.markdown(f'<div class="section-copy">{copy}</div>', unsafe_allow_html=True)


def close_card():
    st.markdown("</div>", unsafe_allow_html=True)


def render_bar_chart(rows, x_key, y_key, color, height=320):
    if not rows:
        return
    chart = (
        alt.Chart(alt.Data(values=rows))
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, color=color)
        .encode(
            x=alt.X(f"{x_key}:N", sort="-y", axis=alt.Axis(title=None, labelAngle=-28, labelLimit=220)),
            y=alt.Y(f"{y_key}:Q", axis=alt.Axis(title=None, grid=True)),
            tooltip=[alt.Tooltip(f"{x_key}:N", title=x_key), alt.Tooltip(f"{y_key}:Q", title=y_key)],
        )
        .properties(height=height)
        .configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor="#42526b",
            titleColor="#42526b",
            gridColor="rgba(82, 96, 122, 0.16)",
            domainColor="rgba(82, 96, 122, 0.24)",
            tickColor="rgba(82, 96, 122, 0.24)",
        )
    )
    st.altair_chart(chart, use_container_width=True)


def get_db_setup():
    if "db_setup" not in st.session_state:
        st.session_state.db_setup = DatabaseSetup()
    return st.session_state.db_setup


def get_recommender():
    db_setup = get_db_setup()
    if "recommender" not in st.session_state:
        st.session_state.recommender = ProductRecommender(db_setup.driver, db_setup.database)
    return st.session_state.recommender


def fetch_graph_stats(db_setup):
    with db_setup.driver.session(database=db_setup.database) as session:
        total_nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        total_rels = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    return total_nodes, total_rels


def fetch_demo_users(db_setup, limit=30):
    query = """
    MATCH (u:User)-[:PURCHASED]->(p:Product)
    WITH u, count(p) AS purchased_count
    ORDER BY purchased_count DESC, u.id
    LIMIT $limit
    RETURN u.id AS user_id, coalesce(u.display_name, u.name, u.id) AS user_name, purchased_count
    """
    with db_setup.driver.session(database=db_setup.database) as session:
        rows = session.run(query, limit=limit)
        return [dict(row) for row in rows]


def fetch_user_profile(db_setup, user_id):
    query = """
    MATCH (u:User {id: $user_id})
    OPTIONAL MATCH (u)-[:PURCHASED]->(p:Product)
    RETURN u.id AS user_id,
           coalesce(u.display_name, u.name, u.id) AS user_name,
           count(p) AS purchased_count
    """
    with db_setup.driver.session(database=db_setup.database) as session:
        row = session.run(query, user_id=user_id).single()
        return dict(row) if row and row["user_id"] else None


def fetch_user_recent_purchases(db_setup, user_id, limit=15):
    query = """
    MATCH (u:User {id: $user_id})-[:PURCHASED]->(p:Product)-[:BELONGS_TO]->(c:Category)
    RETURN p.title AS product_name, c.name AS category
    ORDER BY product_name
    LIMIT $limit
    """
    with db_setup.driver.session(database=db_setup.database) as session:
        rows = session.run(query, user_id=user_id, limit=limit)
        return [dict(row) for row in rows]


def fetch_user_top_categories(db_setup, user_id, limit=5):
    query = """
    MATCH (u:User {id: $user_id})-[:PURCHASED]->(:Product)-[:BELONGS_TO]->(c:Category)
    RETURN c.name AS category, count(*) AS purchases
    ORDER BY purchases DESC, category
    LIMIT $limit
    """
    with db_setup.driver.session(database=db_setup.database) as session:
        rows = session.run(query, user_id=user_id, limit=limit)
        return [dict(row) for row in rows]


def fetch_liked_categories(db_setup, user_id, limit=10):
    query = """
    MATCH (u:User {id: $user_id})-[r]->(c:Category)
    WHERE type(r) = 'LIKES_CATEGORY'
    RETURN c.name AS category,
           coalesce(r.purchase_count, 0) AS purchase_count,
           coalesce(r.score, 0) AS score
    ORDER BY score DESC, category
    LIMIT $limit
    """
    with db_setup.driver.session(database=db_setup.database) as session:
        rows = session.run(query, user_id=user_id, limit=limit)
        return [dict(row) for row in rows]


def fetch_similar_users(db_setup, user_id, limit=10):
    query = """
    MATCH (u:User {id: $user_id})-[r]-(other:User)
    WHERE type(r) = 'SIMILAR_TO'
    RETURN other.id AS similar_user_id,
           coalesce(other.display_name, other.name, other.id) AS similar_user_name,
           coalesce(r.shared_products, 0) AS shared_products
    ORDER BY shared_products DESC, similar_user_id
    LIMIT $limit
    """
    with db_setup.driver.session(database=db_setup.database) as session:
        rows = session.run(query, user_id=user_id, limit=limit)
        return [dict(row) for row in rows]


def fetch_co_purchased_relationships(db_setup, user_id, limit=10):
    query = """
    MATCH (u:User {id: $user_id})-[:PURCHASED]->(owned:Product)
    MATCH (owned)-[r]-(cand:Product)
    WHERE type(r) = 'CO_PURCHASED_WITH'
      AND NOT (u)-[:PURCHASED]->(cand)
    RETURN owned.title AS owned_product,
           cand.title AS recommended_product,
           coalesce(r.co_user_count, 0) AS co_user_count
    ORDER BY co_user_count DESC, owned_product, recommended_product
    LIMIT $limit
    """
    with db_setup.driver.session(database=db_setup.database) as session:
        rows = session.run(query, user_id=user_id, limit=limit)
        return [dict(row) for row in rows]


def fetch_relationship_counts(db_setup):
    query = """
    MATCH ()-[r]->()
    WHERE type(r) IN ['PURCHASED', 'BELONGS_TO', 'LIKES_CATEGORY', 'SIMILAR_TO', 'CO_PURCHASED_WITH', 'INTERESTED_IN', 'SIMILAR_CATEGORY_TASTE']
    RETURN type(r) AS relation_type, count(*) AS total
    ORDER BY total DESC, relation_type
    """
    with db_setup.driver.session(database=db_setup.database) as session:
        rows = session.run(query)
        return [dict(row) for row in rows]


def format_recommendation_rows(rows):
    return [
        {
            "Rank": index,
            "Recommended Product": row["product"],
            "Score": row["score"],
            "Strategy": row["strategy"],
            "Reason": row["reason"],
        }
        for index, row in enumerate(rows, start=1)
    ]


apply_dashboard_theme()

st.title("Neo4j Product Recommendation")
st.caption("Interactive demo: pick a user, review purchase history, and inspect recommendation reasons.")

try:
    db_setup = get_db_setup()
    total_nodes, total_rels = fetch_graph_stats(db_setup)
    demo_users = fetch_demo_users(db_setup)
    relationship_counts = fetch_relationship_counts(db_setup)
except Exception as exc:
    st.error(f"Could not connect to Neo4j or read graph data: {exc}")
    st.stop()

with st.sidebar:
    st.header("Demo Settings")
    top_n = st.slider("Number of recommendations", min_value=1, max_value=20, value=5, step=1)
    typed_user_id = st.text_input("Enter User ID", value="", placeholder="Example: 1")
    demo_user_options = [f"{u['user_id']} | {u['user_name']} ({u['purchased_count']} purchases)" for u in demo_users]
    selected_demo_user = st.selectbox(
        "Or pick a demo user",
        options=demo_user_options if demo_user_options else ["No demo users available"],
        index=0,
    )
    run_btn = st.button("Run Recommendation", type="primary", use_container_width=True)

stats_col1, stats_col2 = st.columns(2)
stats_col1.metric("Total nodes", total_nodes)
stats_col2.metric("Total relationships", total_rels)

if relationship_counts:
    open_card("Graph Overview", "This chart helps you read the relationship mix in the current Neo4j graph.")
    render_bar_chart(relationship_counts, "relation_type", "total", CHART_COLORS["graph"], height=280)
    close_card()

effective_user_id = typed_user_id.strip()
if not effective_user_id and demo_users:
    effective_user_id = selected_demo_user.split("|", 1)[0].strip()

if run_btn:
    if not effective_user_id:
        st.warning("Please enter a user ID or pick one of the demo users.")
        st.stop()

    profile = fetch_user_profile(db_setup, effective_user_id)
    if not profile:
        st.error(f"Could not find user_id = {effective_user_id} in the graph.")
        st.stop()

    if profile["purchased_count"] == 0:
        st.warning(f"User {effective_user_id} exists but has no PURCHASED relationships yet.")
        st.stop()

    st.subheader(f"User Profile: {profile['user_id']}")
    p1, p2 = st.columns(2)
    p1.metric("Display name", profile["user_name"])
    p2.metric("Purchased products", profile["purchased_count"])

    purchase_col, category_col = st.columns(2)
    with purchase_col:
        open_card("Recent Purchases", "A quick sample of what this user has already bought.")
        purchases = fetch_user_recent_purchases(db_setup, effective_user_id, limit=15)
        st.table(purchases if purchases else [{"product_name": "No data", "category": "-"}])
        close_card()
    with category_col:
        open_card("Top Categories", "These categories drive the strongest recommendation signals for the selected user.")
        top_categories = fetch_user_top_categories(db_setup, effective_user_id, limit=5)
        st.table(top_categories if top_categories else [{"category": "No data", "purchases": 0}])
        close_card()

    if top_categories:
        open_card("Category Preference Chart", "Category volume is shown as a compact profile of user taste.")
        render_bar_chart(top_categories, "category", "purchases", CHART_COLORS["category"], height=300)
        close_card()

    recommender = get_recommender()
    with st.spinner("Generating recommendations and explanation..."):
        user_based = recommender.get_user_based_recommendation_details(effective_user_id, top_n=top_n)
        category_based = recommender.get_category_based_recommendation_details(effective_user_id, top_n=top_n)

    col1, col2 = st.columns(2)
    with col1:
        open_card("User-based Recommendation", "Recommendations influenced by similar users and shared purchase behavior.")
        if user_based:
            st.dataframe(format_recommendation_rows(user_based), use_container_width=True, hide_index=True)
        else:
            st.info("No user-based recommendation was generated for this user.")
        close_card()
    with col2:
        open_card("Category-based Recommendation", "Recommendations influenced by the user's strongest product categories.")
        if category_based:
            st.dataframe(format_recommendation_rows(category_based), use_container_width=True, hide_index=True)
        else:
            st.info("No category-based recommendation was generated for this user.")
        close_card()

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        if user_based:
            open_card("User-based Score Chart", "Higher bars indicate stronger recommendation confidence from collaborative signals.")
            render_bar_chart(format_recommendation_rows(user_based), "Recommended Product", "Score", CHART_COLORS["user_reco"])
            close_card()
    with chart_col2:
        if category_based:
            open_card("Category-based Score Chart", "This view emphasizes category-driven ranking strength.")
            render_bar_chart(format_recommendation_rows(category_based), "Recommended Product", "Score", CHART_COLORS["category_reco"])
            close_card()

    st.subheader("Relationship Explorer")
    rel_col1, rel_col2, rel_col3 = st.columns(3)

    liked_categories = fetch_liked_categories(db_setup, effective_user_id, limit=10)
    similar_users = fetch_similar_users(db_setup, effective_user_id, limit=10)
    co_purchased_relationships = fetch_co_purchased_relationships(db_setup, effective_user_id, limit=10)

    with rel_col1:
        open_card("LIKES_CATEGORY", "Derived category affinity for the current user.")
        if liked_categories:
            st.dataframe(liked_categories, use_container_width=True, hide_index=True)
        else:
            st.info("No LIKES_CATEGORY relationships found for this user.")
        close_card()

    with rel_col2:
        open_card("SIMILAR_TO", "Users who share overlapping product purchase behavior.")
        if similar_users:
            st.dataframe(similar_users, use_container_width=True, hide_index=True)
        else:
            st.info("No SIMILAR_TO relationships found for this user.")
        close_card()

    with rel_col3:
        open_card("CO_PURCHASED_WITH Paths", "Owned products that connect to recommendation candidates through co-purchase behavior.")
        if co_purchased_relationships:
            st.dataframe(co_purchased_relationships, use_container_width=True, hide_index=True)
        else:
            st.info("No CO_PURCHASED_WITH recommendation paths found for this user.")
        close_card()

    if not user_based and not category_based:
        st.warning("No recommendation was generated. Try another demo user from the sidebar.")
