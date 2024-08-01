import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Layout from '@/components/Layout';
import styles from '@/styles/Auth.module.css';
import { FaGoogle, FaFacebook } from 'react-icons/fa';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [staySignedIn, setStaySignedIn] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    const token = router.query.token;
    if (token) {
      localStorage.setItem('token', token);
      router.push('/list-users');
    }
  }, [router]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, stay_signed_in: staySignedIn }),
      });
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.token);
        router.push('/list-users');
      } else {
        const data = await response.json();
        setError(data.message);
      }
    } catch (error) {
      setError('An error occurred. Please try again.');
    }
  };

  const handleSocialLogin = (provider) => {
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/${provider}`;
  };

  return (
    <Layout>
      <div className={styles.authContainer}>
        <h1>Sign In</h1>
        <form className={styles.form} onSubmit={handleSubmit}>
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
          <div className={styles.formOptions}>
            <label>
              <input
                type="checkbox"
                checked={staySignedIn}
                onChange={(e) => setStaySignedIn(e.target.checked)}
              />
              Stay signed in
            </label>
            <Link href="/forgot-password">Forgot Password?</Link>
          </div>
          <button type="submit" className={styles.submitButton}>SIGN IN</button>
        </form>
        {error && <p className={styles.error}>{error}</p>}
        <div className={styles.socialLogin}>
          <p>Or Sign In with</p>
          <div className={styles.socialButtons}>
            <button onClick={() => handleSocialLogin('google')}><FaGoogle /></button>
            <button onClick={() => handleSocialLogin('facebook')}><FaFacebook /></button>
          </div>
        </div>
        <p className={styles.signupPrompt}>
          Not a member? <Link href="/signup">Sign Up</Link>
        </p>
      </div>
    </Layout>
  );
}