import streamlit as st

st.title("My Cloud Control App 🚀")

# if st.button("Click Me"):
#     st.write("Button Clicked! 🎉")
    
# Using object notation
# add_selectbox = st.sidebar.selectbox(
#     "How would you like to be contacted?",
#     ("Email", "Home phone", "Mobile phone")
# )

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
        



with st.expander("ECS"):
    st.divider()
    col1, col2, col3 = st.columns(3)
    #st.header("ECS Tasks")
    with col1:
        if st.button("Trigger Price Check", use_container_width=True):
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
        
