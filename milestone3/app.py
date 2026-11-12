import milestone3_dashboard
from components import working as working
import streamlit as st

st.set_page_config(
    page_title="Operating System Simulator",
    page_icon="💻",
    layout="wide"
)

st.markdown("""
<style>

/* Main dashboard */
.stApp {
    background-color: #171A21;
    color: #D6D9E0;
}

/* Regular text */
.stApp p,
.stApp span,
.stApp label {
    color: #D6D9E0;
}

/* Headings */
h1, h2, h3 {
    color: #DDE1E7 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #11141A;
    border-right: 1px solid #343A46;
}

/* Sidebar text */
section[data-testid="stSidebar"] * {
    color: #CDD1D8;
}

/* Selected navigation */
div[role="radiogroup"] label:has(input:checked) {
    color: #62B6B7 !important;
    font-weight: 700;
}

/* Buttons */
.stButton > button {
    background-color: #252A34;
    color: #DDE1E7;
    border: 1px solid #62B6B7;
    border-radius: 7px;
}

.stButton > button:hover {
    background-color: #3D8587;
    color: #E4E7EB;
    border-color: #62B6B7;
}

/* Input boxes */
input, textarea {
    background-color: #252A34 !important;
    color: #D6D9E0 !important;
}

/* Metric values */
[data-testid="stMetricValue"] {
    color: #DDE1E7;
}

/* Metric labels */
[data-testid="stMetricLabel"] {
    color: #AEB4BE;
}

/* Dividers */
hr {
    border-color: #343A46;
}

/* Captions */
[data-testid="stCaptionContainer"] {
    color: #AEB4BE;
}

/* Dashboard metric cards */
div[data-testid="stMetric"] {
    background-color: #20252E;
    border: 1px solid #343A46;
    padding: 18px;
    border-radius: 10px;
}

div[data-testid="stMetric"]:hover {
    border-color: #62B6B7;
}

</style>
""", unsafe_allow_html=True)

st.title("Operating System Simulator")
st.caption("Interactive dashboard for configuring, testing, and analyzing OS simulations.")

page = st.sidebar.radio(
    "Navigation",
  [
    "Overview",
    "Process Manager",
    "Memory Manager",
    "File Manager",
    "Security Manager",
    "Device Manager",
    "Network Manager",
    "Parallel Computing",
    "Scenario Builder",
    "Testing Center",
    "Results",
    "Milestone 3 Overview",
    "CPU Scheduling (Updated)",
    "Memory Manager (Milestone 3)",
    "File System",
    "Policy Comparison",
    "Dashboard Tests",
    "Exports"
]
)

if page == "Overview":
    working.overview_page()

elif page == "Process Manager":
    working.process_page()

elif page == "Memory Manager":
    working.memory_page()

elif page == "File Manager":
    working.file_page()

elif page == "Security Manager":
    st.header("Security Manager")
    st.write("Configure and test simulated users, permissions, and security events.")

    st.subheader("User Session")

    col1, col2 = st.columns(2)

    with col1:
        security_user = st.selectbox(
            "User",
            ["admin", "user1", "user2"]
        )

    with col2:
        security_role = st.selectbox(
            "Role",
            ["Administrator", "Standard User"]
        )

    col1, col2 = st.columns(2)

    with col1:
        st.button("Login")

    with col2:
        st.button("Logout")

    st.divider()

    st.subheader("Permission Management")

    col1, col2, col3 = st.columns(3)

    with col1:
        resource = st.text_input(
            "Resource",
            "/docs/notes.txt"
        )

    with col2:
        permission = st.selectbox(
            "Permission",
            ["Read", "Write", "Execute"]
        )

    with col3:
        permission_action = st.selectbox(
            "Action",
            ["Grant", "Revoke"]
        )

    st.button("Apply Permission")

    st.divider()

    st.subheader("Security Status")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Successful Logins", "0")

    with col2:
        st.metric("Failed Logins", "0")

    with col3:
        st.metric("Denied Actions", "0")

    with col4:
        st.metric("Security Alerts", "0")

    st.divider()

    st.subheader("Permission Matrix")

    st.info(
        "User and role permissions will be displayed here."
    )

    st.subheader("Security Event Log")

    st.info(
        "Authentication, authorization, policy changes, "
        "denied actions, and security alerts will appear here."
    )

elif page == "Device Manager":
    st.header("Device Manager")
    st.write("Configure and test simulated device requests and scheduling.")

    st.subheader("Device Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        device_type = st.selectbox(
            "Device",
            ["Disk", "Printer", "Keyboard"]
        )

    with col2:
        device_policy = st.selectbox(
            "Scheduling Policy",
            ["FCFS", "SSTF", "SCAN"]
        )

    with col3:
        device_state = st.selectbox(
            "Device State",
            ["Available", "Busy", "Offline", "Error"]
        )

    st.divider()

    st.subheader("Device Request")

    col1, col2, col3 = st.columns(3)

    with col1:
        request_id = st.text_input(
            "Request ID",
            "R1"
        )

    with col2:
        requesting_process = st.text_input(
            "Process ID",
            "P1",
            key="device_process"
        )

    with col3:
        service_time = st.number_input(
            "Service Time (ms)",
            min_value=1,
            value=5
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.button("Add Request")

    with col2:
        st.button("Run Device Test")

    with col3:
        st.button("Reset Device Manager")

    st.divider()

    st.subheader("Device Status")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Queued Requests", "0")

    with col2:
        st.metric("Completed", "0")

    with col3:
        st.metric("Failures", "0")

    with col4:
        st.metric("Utilization", "0%")

    st.divider()

    st.subheader("Device Queue")

    st.info(
        "Queued, active, completed, failed, and canceled "
        "requests will appear here."
    )

    st.subheader("Request Timeline")

    st.info(
        "Device request and service timeline will appear here."
    )

    st.subheader("Disk Head Movement")

    st.info(
        "Disk scheduling visualization will appear here "
        "when a disk policy is selected."
    )

elif page == "Network Manager":
    st.header("Network Manager")
    st.write("Configure and test simulated network traffic and routing.")

    st.subheader("Network Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        network_policy = st.selectbox(
            "Packet Scheduling Policy",
            ["FIFO", "Priority Queue"]
        )

    with col2:
        routing_method = st.selectbox(
            "Routing Method",
            ["Shortest Hop", "Static Routing"]
        )

    with col3:
        buffer_capacity = st.number_input(
            "Buffer Capacity",
            min_value=1,
            value=10
        )

    st.divider()

    st.subheader("Packet Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        packet_id = st.text_input(
            "Packet ID",
            "PKT1"
        )

    with col2:
        source_node = st.selectbox(
            "Source Node",
            ["Node A", "Node B", "Node C"]
        )

    with col3:
        destination_node = st.selectbox(
            "Destination Node",
            ["Node A", "Node B", "Node C"],
            index=1
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        packet_size = st.number_input(
            "Packet Size (bytes)",
            min_value=1,
            value=512
        )

    with col2:
        packet_priority = st.number_input(
            "Packet Priority",
            min_value=1,
            value=1
        )

    with col3:
        packet_ttl = st.number_input(
            "TTL",
            min_value=1,
            value=10
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.button("Add Packet")

    with col2:
        st.button("Run Network Test")

    with col3:
        st.button("Reset Network Manager")

    st.divider()

    st.subheader("Network Status")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Packets Sent", "0")

    with col2:
        st.metric("Delivered", "0")

    with col3:
        st.metric("Dropped", "0")

    with col4:
        st.metric("Link Utilization", "0%")

    st.divider()

    st.subheader("Network Topology")

    st.code(
        """Node A -------- Node B
   \\              /
    \\            /
       Node C"""
    )

    st.subheader("Packet Timeline")

    st.info(
        "Packet transmission, delivery, queueing, and "
        "drop events will appear here."
    )

    st.subheader("Network Results")

    st.info(
        "Throughput, delay, delivery rate, drop rate, "
        "and link utilization will appear here."
    )
elif page == "Parallel Computing":
    working.parallel_page()

elif page == "Scenario Builder":
    working.scenario_page()

elif page == "Testing Center":
    working.testing_page()

elif page == "Results":
    working.results_page()


elif page in ("Milestone 3 Overview", "CPU Scheduling (Updated)", "Memory Manager (Milestone 3)", "File System", "Policy Comparison", "Dashboard Tests", "Exports"):
    milestone3_dashboard.render(page)
