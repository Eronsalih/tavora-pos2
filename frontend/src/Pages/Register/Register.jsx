import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Register.css";

import { signupUser, loginUser } from "../../services/authService";
import { useAuth } from "../../context/AuthContext";

function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    business_name: "",
    name: "",
    email: "",
    password: "",
    pin: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;

    setFormData((currentData) => ({
      ...currentData,
      [name]: value,
    }));

    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (
      !formData.business_name ||
      !formData.name ||
      !formData.email ||
      !formData.password ||
      !formData.pin
    ) {
      setError("Plotëso të gjitha fushat.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      await signupUser({
        business_name: formData.business_name.trim(),
        name: formData.name.trim(),
        email: formData.email.trim(),
        password: formData.password,
        pin: formData.pin,
      });

      const authenticationData = await loginUser({
        email: formData.email.trim(),
        password: formData.password,
      });

      login(authenticationData);

      navigate("/", {
        replace: true,
      });
    } catch (error) {
      console.error("Registration failed:", error);

      setError(error.response?.data?.detail || "Regjistrimi dështoi.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        background: "#f5f6fb",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          width: "100%",
          maxWidth: "420px",
          background: "white",
          padding: "32px",
          borderRadius: "16px",
        }}
      >
        <h1>Create Tavora Account</h1>

        <input
          type="text"
          name="name"
          placeholder="Emri"
          value={formData.name}
          onChange={handleChange}
        />

        <input
          type="text"
          name="business_name"
          placeholder="Emri i firmës"
          value={formData.business_name}
          onChange={handleChange}
        />

        <input
          type="email"
          name="email"
          placeholder="Email"
          value={formData.email}
          onChange={handleChange}
        />

        <input
          type="password"
          name="password"
          placeholder="Password"
          value={formData.password}
          onChange={handleChange}
        />
        <input
          type="password"
          name="pin"
          placeholder="PIN 4-shifror"
          maxLength={4}
          inputMode="numeric"
          value={formData.pin}
          onChange={handleChange}
        />
        {error && <p>{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? "Creating..." : "Create Account"}
        </button>

        <button type="button" onClick={() => navigate("/login")}>
          Back to Login
        </button>
      </form>
    </main>
  );
}

export default Register;
