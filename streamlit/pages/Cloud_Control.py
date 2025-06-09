from functions import ecs, widgets
import streamlit as st

widgets.show_pages_sidebar()


st.title("My Cloud Control App 🚀")
        
def trigger_price_check():
    print("Price check triggered")

# Using "with" notation
with st.sidebar:
    st.header("Sidebar")
    with st.expander("AWS Shortcuts"):
        st.link_button("AWS Dashboard", "https://us-east-1.console.aws.amazon.com/console/home?region=us-east-1", use_container_width=True)
        st.link_button("ECS Dashboard", "https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#Home:", use_container_width=True)
        st.link_button("EC2 Dashboard", "https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#Home:", use_container_width=True)

    with st.expander("TCG Shortcuts"):
        st.link_button("TCGPlayer Seller Portal", "https://store.tcgplayer.com/admin/Seller/Dashboard/22821dc8", use_container_width=True)
        st.link_button("TCGPlayer Buyer Site", "https://www.tcgplayer.com/", use_container_width=True)
    
    with st.expander("AWS Things To Play With"):
        st.checkbox("ECS")
        st.checkbox("EC2")
        st.checkbox("ECR")
        st.checkbox("Lambda")
        
    with st.expander("Other"):
        st.link_button("Streamlit API", "https://docs.streamlit.io/develop/api-reference", use_container_width=True)

with st.expander("ECS"):
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Trigger Price Check", use_container_width=True):
            task_arn = ecs.run_ecs_task()
    with col2:
        pass
    with col3:
        pass

with st.expander("Price Check"):
    st.divider()

    # Initialize options in session state
    if "options" not in st.session_state:
        st.session_state.options = []

    st.subheader("Add a new card")

    # Create 3 columns
    col1, col2, col3 = st.columns([2, 3, 1])

    # Inputs and button
    with col1:
        new_name = st.text_input("Card Name",placeholder="Card Name", key="Card name", label_visibility="collapsed")

    with col2:
        new_url = st.text_input("URL", key="url_input", placeholder="URL", label_visibility="collapsed")

    with col3:
        if st.button("Add", use_container_width=True):
            if new_name and new_url:
                new_entry = (new_name.strip(), new_url.strip())
                if new_entry not in st.session_state.options:
                    st.session_state.options.append(new_entry)
                else:
                    st.warning("That option already exists.")
            else:
                st.error("Both name and URL are required.")

        
    # Display checkboxes
    st.subheader("Select Options")
    checkbox_states = {}

    for name, url in st.session_state.options:
        checkbox_states[name] = st.checkbox(name, key=name)

    # Show selected links
    st.subheader("You selected:")
    for name, url in st.session_state.options:
        if checkbox_states.get(name):
            st.markdown(f"- [{name}]({url})")
        
                
    if st.button("Run Price Check"):
        trigger_price_check()