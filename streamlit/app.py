import streamlit as st

st.title("My Cloud Control App 🚀")

import streamlit as st

tab1, tab2, tab3 = st.tabs(["Cat", "Dog", "Owl"])

with tab1:
    st.header("A cat")
    st.image("https://static.streamlit.io/examples/cat.jpg", width=200)
with tab2:
    st.header("A dog")
    st.image("https://static.streamlit.io/examples/dog.jpg", width=200)
with tab3:
    st.header("An owl")
    st.image("https://static.streamlit.io/examples/owl.jpg", width=200)

# Using "with" notation
with st.sidebar:
    st.header("Sidebar")
    # add_radio = st.radio(
    #     "Choose a shipping method",
    #     ("Standard (5-15 days)", "Express (2-5 days)")
    # )
    # st.checkbox(
    #     "test"
    # )
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
            st.audio("maro-jump-sound-effect_1.mp3", format="audio/mp3", autoplay=True)
            st.write("Expander Test")
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

        
def trigger_price_check():
    ...



def page2():
    st.title("Second page")

pg = st.navigation([
    st.Page("page_1.py", title="First page", icon="🔥"),
    st.Page(page2, title="Second page", icon=":material/favorite:"),
])
pg.run()

# if st.button("Click Me"):
#     st.write("Button Clicked! 🎉")
    
# Using object notation
# add_selectbox = st.sidebar.selectbox(
#     "How would you like to be contacted?",
#     ("Email", "Home phone", "Mobile phone")
# )