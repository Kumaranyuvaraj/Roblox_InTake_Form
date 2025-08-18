import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import Footer from '../components/Footer';

// Import images
import logoNextkeyWhite from '../assets/img/logo-Nextkey-white.png';
import arrowUpRight from '../assets/img/arrowUpRight.svg';

const KidsPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    description: ''
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: false }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!formData.name.trim()) newErrors.name = true;
    if (!formData.email.trim()) {
      newErrors.email = true;
    } else if (!emailRegex.test(formData.email)) {
      newErrors.email = true;
    }

    return newErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newErrors = validateForm();
    
    if (Object.keys(newErrors).length === 0) {
      setIsSubmitting(true);
      
      try {
        // API endpoint for submitting kids page leads
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        
        const submitData = {
          name: formData.name,
          email: formData.email,
          description: formData.description,
          lead_source: 'kids',
          // Pass the original domain where the form was submitted
          original_domain: window.location.hostname
        };

        const response = await fetch(`${apiUrl}/api/landing-page-leads/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(submitData),
        });

        if (response.ok) {
          const result = await response.json();
          console.log('Lead submitted successfully:', result);
          
          // Show success toast before redirecting
          toast.success('Your request has been submitted successfully! Redirecting...');
          
          // Small delay to show the toast before redirecting
          setTimeout(() => {
            navigate('/thank-you');
          }, 1000);
        } else {
          const errorData = await response.json();
          console.error('Submission error:', errorData);
          
          // Handle validation errors from backend
          if (errorData.non_field_errors) {
            toast.error(errorData.non_field_errors[0]);
          } else if (errorData.email) {
            toast.error(errorData.email[0]);
          } else if (errorData.name) {
            toast.error(errorData.name[0]);
          } else {
            toast.error('There was an error submitting your request. Please try again.');
          }
        }
      } catch (error) {
        console.error('Network error:', error);
        toast.error('Unable to connect to server. Please check your internet connection and try again.');
      } finally {
        setIsSubmitting(false);
      }
    } else {
      setErrors(newErrors);
    }
  };

  return (
    <div className="container-fluid px-0">
      <section className="container-fluid kids-hero">
        <div className="container">
          <div className="row">
            <div className="col-12">
              <div className="logo">
                <img src={logoNextkeyWhite} alt="NextKey Litigation" className="img-fluid" />
              </div>
            </div>
          </div>
          <div className="row">
            <div className="col-12 col-lg-6 col-xl-7">
              <h1 className="kids-hero-title">Safe Gaming Starts Here!</h1>
              <p className="kids-hero-subtitle pb-5">Fun is better when it's safe — for you and your friends.</p>
            </div>
            <div className="col-12 col-lg-6 col-xl-5 kids-form">
              <div className="form-box">
                <h4 className="font-popins mb-3">Get Help Together</h4>
                <p className="font-popins">
                  If you think something's wrong, ask your parent or guardian to fill out this form. 
                  We'll help make your gaming experience safe again.
                </p>
                <form className="form-container" onSubmit={handleSubmit} noValidate>
                  <div className="mb-3">
                    <label htmlFor="name" className="form-label">Parent/Guardian Full Name</label>
                    <input
                      type="text"
                      className={`form-control ${errors.name ? 'is-invalid' : ''}`}
                      id="name"
                      name="name"
                      placeholder="John Doe"
                      value={formData.name}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="mb-3">
                    <label htmlFor="email" className="form-label">Email</label>
                    <input
                      type="email"
                      className={`form-control ${errors.email ? 'is-invalid' : ''}`}
                      id="email"
                      name="email"
                      placeholder="your.name@domain.com"
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="mb-3">
                    <label htmlFor="description" className="form-label">Short description of your concern</label>
                    <textarea
                      className="form-control"
                      id="description"
                      name="description"
                      rows="2"
                      placeholder="Brief about your concern"
                      value={formData.description}
                      onChange={handleInputChange}
                    />
                  </div>
                  <button type="submit" className="btn btn-guidance w-100" disabled={isSubmitting}>
                    {isSubmitting ? 'Submitting...' : 'Send to GameGuard Legal'} <img src={arrowUpRight} alt="Arrow" />
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section-sefty">
        <div className="container">
          <div className="row">
            <div className="col-12 col-lg-6 pt-5">
              <h1 className="kids-section-title">Why Safety Matters</h1>
              <ul>
                <li className="list-text">Keep your games fun and fair.</li>
                <li className="list-text">Avoid strangers or tricky messages in chat.</li>
                <li className="list-text">Know what to do if something feels wrong.</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="what-you-can-do">
        <div className="container">
          <div className="row">
            <div className="col-12 col-lg-6 pt-5">
              <h1 className="kids-section-title">What You Can Do</h1>
              <ul>
                <li className="list-text">Always talk to a parent if something online feels strange.</li>
                <li className="list-text">Don't click links from people you don't know.</li>
                <li className="list-text">Keep your personal information private.</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default KidsPage;
