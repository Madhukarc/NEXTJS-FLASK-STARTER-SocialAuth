import { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Layout from '@/components/Layout';
import styles from '@/styles/Auth.module.css';
import { FaGoogle, FaFacebook } from 'react-icons/fa';

export default function SignupPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords don't match");
      return;
    }
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      });
      if (response.ok) {
        router.push('/login');
      } else {
        const data = await response.json();
        setError(data.message);
      }
    } catch (error) {
      setError('An error occurred. Please try again.');
    }
  };

  const handleSocialSignup = (provider) => {
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/${provider}`;
  };

  return (
    <Layout>
      <div className={styles.authContainer}>
        <h1>Sign Up</h1>
        <form className={styles.form} onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Full Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
          <button type="submit" className={styles.submitButton}>SIGN UP</button>
        </form>
        {error && <p className={styles.error}>{error}</p>}
        <div className={styles.socialLogin}>
          <p>Or Sign Up with</p>
          <div className={styles.socialButtons}>
            <button onClick={() => handleSocialSignup('google')}><FaGoogle /></button>
            <button onClick={() => handleSocialSignup('facebook')}><FaFacebook /></button>
          </div>
        </div>
        <p className={styles.loginPrompt}>
          Already have an account? <Link href="/login">Log In</Link>
        </p>
      </div>
    </Layout>
  );
}