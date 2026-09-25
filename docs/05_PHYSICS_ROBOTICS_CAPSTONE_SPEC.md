# 🤖 Industrial Capstone Specification: Physics to Robotics & Simulation

> **Showcase Domain**: Physics-to-Tech Career Pipeline  
> **Target Career Role**: Robotics & Autonomous Physical Simulation Engineer  
> **Key Disciplines**: Classical Mechanics, Kinematics, Dynamics, Numerical Methods, URDF, PyBullet & ROS 2

---

## 1. Why the Physics-to-Robotics Track Wins at SIH

Most student teams pick generic web development roles (*"MERN Stack Developer"*). By anchoring our showcase in **Physics + Robotics Software Engineering**, CareerLattice AI demonstrates:
1. **Multi-Disciplinary Innovation**: Directly supports **NEP 2020** mandates for interdisciplinary learning (marrying pure sciences with computer science).
2. **High-Growth Enterprise Alignment**: Directly feeds talent into high-value Indian sectors—**Electric Vehicles (Ather Energy, Ola Electric), Warehouse Robotics (GreyOrange), and Defense/Aerospace (DRDO, ISRO vendors)**.
3. **Deep Graph Prerequisite Logic**: Physics concepts have strict mathematical dependencies (Kinematics $\rightarrow$ Rigid Body Dynamics $\rightarrow$ Robot Simulation $\rightarrow$ Sensor Fusion $\rightarrow$ Path Planning).

---

## 2. The Prescribed Industrial Capstone Project

To bridge the gap between watching lectures and getting hired, CareerLattice generates a **4-Milestone Production Blueprint**:

### 🏆 Project Title:
**"Autonomous Mobile Robot (AMR): 2D/3D Kinematic Physics Simulator with LiDAR Sensor Fusion & Obstacle Avoidance in ROS 2"**

---

### Milestone 1: Kinematic Physics Engine (Pure Python / NumPy)
* **Objective**: Model the mathematical physics of a two-wheeled differential drive mobile robot.
* **Physics Formulations**:
  * Forward Kinematics:
    $$\dot{x} = v \cos(\theta), \quad \dot{y} = v \sin(\theta), \quad \dot{\theta} = \omega$$
    $$v = \frac{r}{2}(\omega_R + \omega_L), \quad \omega = \frac{r}{L}(\omega_R - \omega_L)$$
  * Fourth-Order Runge-Kutta (RK4) numerical integrator for velocity and position ODEs.
* **Artifacts Created**: `kinematics_engine.py`, `rk4_integrator.py`.
* **Tree-sitter Verification**: Checks for `numpy` matrix operations, trigonometry calls, and time-step loops.

---

### Milestone 2: URDF Robot Specification & PyBullet Physics Sandbox
* **Objective**: Define the physical properties of the robot in standard XML/URDF format and simulate in PyBullet.
* **Physics Formulations**:
  * Rigid body mass properties, moments of inertia ($I_{xx}, I_{yy}, I_{zz}$), wheel friction coefficients, and center-of-mass offsets.
* **Artifacts Created**: `urdf/amr_robot.urdf`, `simulation_sandbox.py`.
* **Tree-sitter Verification**: Verifies presence of a valid `.urdf` file containing `<inertial>`, `<collision>`, and `<joint>` tags.

---

### Milestone 3: Sensor Ray-Casting & Extended Kalman Filter (EKF)
* **Objective**: Simulate noisy real-world physics and implement state estimation.
* **Physics Formulations**:
  * 360-degree LiDAR distance ray-casting against bounding boxes.
  * Adding Gaussian noise $\mathcal{N}(0, \sigma^2)$ to wheel encoder odometry.
  * Extended Kalman Filter (EKF) covariance matrix updates to compute optimal state estimates.
* **Artifacts Created**: `sensor_simulation.py`, `ekf_filter.py`.
* **Tree-sitter Verification**: Detects covariance matrix updates, Kalman gain calculations, and Gaussian noise additions.

---

### Milestone 4: Industry Middleware (ROS 2 Navigation Nodes)
* **Objective**: Package the simulation into production-grade ROS 2 nodes.
* **Architecture**:
  * Subscribe to `/scan` (LiDAR range data).
  * Publish velocity vectors to `/cmd_vel` (`geometry_msgs/Twist`).
  * Obstacle avoidance logic steering the robot through dynamic barriers.
* **Artifacts Created**: `package.xml`, `setup.py`, `nodes/obstacle_avoidance.py`.
* **Tree-sitter Verification**: Verifies `package.xml` build dependency on `rclpy` and presence of ROS 2 publisher/subscriber declarations.

---

## 3. Automated Webhook Re-Verification Matrix

When the candidate completes the capstone and runs `git push origin main`, CareerLattice's webhook triggers the automated code audit:

| Repository File Committed | Abstract Syntax Tree Pattern Detected | Skill Node State Transition |
| :--- | :--- | :--- |
| `kinematics_engine.py` | `numpy.dot()`, `cos()`, `sin()`, differential velocity functions | 🟢 *Robot Kinematics* $\rightarrow$ **VERIFIED (1.0)** |
| `urdf/amr_robot.urdf` | XML tags: `<robot>`, `<link>`, `<inertial>`, `<joint type="continuous">` | 🟢 *URDF Robot Modeling* $\rightarrow$ **VERIFIED (1.0)** |
| `ekf_filter.py` | Matrix operations for state prediction ($P = F P F^T + Q$) | 🟢 *State Estimation (EKF)* $\rightarrow$ **VERIFIED (0.95)** |
| `package.xml` & `nodes/*.py` | `import rclpy`, `create_publisher`, `create_subscription` | 🟢 *ROS 2 Middleware* $\rightarrow$ **VERIFIED (0.90)** |

---

## 4. Unlocked Industrial Job Opportunities (via Open-Source JobSpy)

Once the capstone is verified on GitHub, the system automatically transitions matching job listings from **"Gaps Present"** to **"100% Core Evidence Verified"**:

1. **Ather Energy**: *Autonomous Vehicle Simulation Intern* (Bangalore)
   * Core Requirements: Kinematics, Python/NumPy, URDF, PyBullet, ROS 2.
   * Status: **100% Match Quotient** $\rightarrow$ Active **"Apply Now"** button.
2. **GreyOrange Robotics**: *AMR Dynamics & Simulation Engineer* (Gurgaon)
   * Core Requirements: Classical Mechanics, Rigid Body Physics, Sensor Simulation, ROS 2.
   * Status: **95% Match Quotient** $\rightarrow$ Active **"Apply Now"** button.
