import os
import sys 
import json

from functions import ecs
from functions import  mtg_box_sim

import streamlit as st
import pandas as pd
import numpy as np

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
    #st.header("ECS Tasks")
    with col1:
        if st.button("Trigger Price Check", use_container_width=True):
            task_arn = ecs.run_ecs_task()
            
            st.audio("maro-jump-sound-effect_1.mp3", format="audio/mp3", autoplay=True)
            st.write("{task_arn}")
    with col2:
        if st.button("Other function", use_container_width=True):
            st.write("Expander Test")
    with col3:
        if st.button("Third Function", use_container_width=True):
            st.write("Other Function")       

with st.expander("EC2"):
    st.divider()
    col1, col2, col3 = st.columns(3)
    #st.header("ECS Tasks")
    with col1:
        if st.button("EC2 Button1", use_container_width=True):
            st.write("Expander Test")
    with col2:
        if st.button("EC2 Button2", use_container_width=True):
            st.write("Expander Test")
    with col3:
        if st.button("EC2 Button3", use_container_width=True):
            st.write("Other Function")


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
        
st.title("TCG Tools")
with st.expander("Booster Box EV Calculator"):
    st.divider()
    # Initialize session state to store EV results
    if 'ev_history' not in st.session_state:
        st.session_state.ev_history = []

    # Initialize options in session state
    if "options" not in st.session_state:
        st.session_state.options = []



    # Create 3 columns
    col1, col2, col3 = st.columns([2, 3, 1])

    # Inputs and button
    with col1:
        precon = st.text_input("Set Name",placeholder="dft", value="dft")

    with col2:
        boxes_to_open = st.number_input("Boxes to open", min_value=1, step=1)

    with col3:
        if st.button("Simulate!", use_container_width=True):
            ev = mtg_box_sim.simulate(f"{set}", int(boxes_to_open))
            # Add to history
            st.session_state.ev_history.append({
                "Set": set,
                "Boxes Opened": int(boxes_to_open),
                "EV": round(ev, 2)
            })
        if st.button("clear",use_container_width=True ):
            st.session_state.ev_history = []

    
    
    # Display table with 2 columns
    if st.session_state.ev_history:
        df = pd.DataFrame(st.session_state.ev_history)
        # Center align the entire DataFrame
        styled_data = df.style.set_properties(**{'text-align': 'center'})
        styled_data.set_table_styles([{
            'selector': 'th',
            'props': [('text-align', 'center')]
        }])

        # Display with Streamlit
        st.dataframe(styled_data, use_container_width=True)
        #st.table(df)
                    
with st.expander("Precon EV Calculator"):
    sets = []
    cwd = os.getcwd()  # Get the current working directory
    path = os.path.join(cwd, "data", "precons")  # Construct the full path to the "precons" folder

    precons = []  # Initialize precons list
    for root, dirs, files in os.walk(path):
        sets.extend(dirs)  # Add directories to sets
        precons.extend([file.replace(".txt", "") for file in files])  # Process files and remove ".txt"

    # Clear the precons list if no precons are found
    if not precons:
        precons = []  # Ensure the list is empty

    # Debugging output (optional)
    print(sets)
    print(precons)

    st.divider()
    # Initialize session state to store EV results
    if 'ev_history' not in st.session_state:
        st.session_state.ev_history = []

    # Create 3 columns
    col1, col2, col3 = st.columns([2, 3, 1])

    # Inputs and button
    with col1:
        set_selectbox = st.selectbox(
            "Please select a set code",
            sets,  # Use the dynamically populated sets list
        )

    with col2:
        precon = st.selectbox(
            "Precon Name",
            precons,  # Use the dynamically populated precons list
        )

    with col3:
        st.number_input("EV", min_value=1)