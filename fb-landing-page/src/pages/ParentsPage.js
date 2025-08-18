import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import Footer from '../components/Footer';

// Import images
import logoNextkey from '../assets/img/logo-Nextkey.png';
import iconSafe from '../assets/img/icon-safe.svg';
import iconHealthy from '../assets/img/icon-healthy.svg';
import iconRiskFree from '../assets/img/icon-risk-free.svg';
import arrowRounded from '../assets/img/img-arrow-rounded.svg';
import arrowUpRight from '../assets/img/arrowUpRight.svg';
import boxIconStranger from '../assets/img/box-icon-stranger.svg';
import boxIconInGamePurchase from '../assets/img/box-icon-in-game-purchase.svg';
import boxIconSafety from '../assets/img/box-icon-safty.svg';
import boxIconLegal from '../assets/img/box-icon-legal.svg';
import imgHowWeHelp from '../assets/img/img-how-we-help.png';
import processArrow from '../assets/img/process_arrow.svg';
import imgWhyFamiliesTrustUs from '../assets/img/img-why-families-trust-us.png';

const ParentsPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    stateLocation: '',
    description: ''
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const formatPhoneNumber = (value) => {
    const digits = value.replace(/\D/g, '').substring(0, 10);
    let formatted = '';

    if (digits.length > 0) {
      formatted = '(' + digits.substring(0, 3);
    }
    if (digits.length >= 4) {
      formatted += ') ' + digits.substring(3, 6);
    }
    if (digits.length >= 7) {
      formatted += '-' + digits.substring(6, 10);
    }

    return formatted;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    if (name === 'phone') {
      const formattedPhone = formatPhoneNumber(value);
      setFormData(prev => ({ ...prev, [name]: formattedPhone }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: false }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    const phoneRegex = /^\(\d{3}\)\s\d{3}-\d{4}$/;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!formData.name.trim()) newErrors.name = true;
    if (!formData.email.trim()) {
      newErrors.email = true;
    } else if (!emailRegex.test(formData.email)) {
      newErrors.email = true;
    }
    if (!formData.phone.trim()) {
      newErrors.phone = true;
    } else if (!phoneRegex.test(formData.phone)) {
      newErrors.phone = true;
    }
    if (!formData.stateLocation.trim()) newErrors.stateLocation = true;

    return newErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newErrors = validateForm();
    
    if (Object.keys(newErrors).length === 0) {
      setIsSubmitting(true);
      
      try {
        // API endpoint for submitting parents page leads
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        
        const submitData = {
          name: formData.name,
          email: formData.email,
          phone: formData.phone,
          state_location: formData.stateLocation,
          description: formData.description,
          lead_source: 'parents',
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
      <section className="container pt-4">
        <div className="row">
          <div className="col-12 col-lg-7 col-xl-8 banner-content">
            <div className="logo">
              <img src={logoNextkey} alt="NextKey Litigation" className="img-fluid" />
            </div>
            <h1 className="banner-head font-popins">
              Protect Your Child's Digital World – <span>Get Expert Guidance</span> for Safe Online Gaming
            </h1>
            <p className="banner-text font-popins">
              We work with parents to ensure their child's online gaming experience is
              <span> safe, healthy, and free from risks.</span> If you're concerned about your child's digital safety, our legal experts are here to help.
            </p>
            <div className="banner-icons d-flex align-items-center">
              <img src={iconSafe} alt="Safe" />
              <img src={iconHealthy} alt="Healthy" />
              <img src={iconRiskFree} alt="Risk Free" />
            </div>
            <div className="arrowRounded">
              <img src={arrowRounded} alt="Arrow" />
            </div>
          </div>
          <div className="col-12 col-lg-5 col-xl-4">
            <div className="form-box">
              <h4 className="font-popins mb-3">Request Free Guidance</h4>
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
                  <label htmlFor="phone" className="form-label">Phone</label>
                  <input
                    type="tel"
                    className={`form-control ${errors.phone ? 'is-invalid' : ''}`}
                    id="phone"
                    name="phone"
                    placeholder="(123) 456-7890"
                    value={formData.phone}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="mb-3">
                  <label htmlFor="stateLocation" className="form-label">State/Location</label>
                  <input
                    type="text"
                    className={`form-control ${errors.stateLocation ? 'is-invalid' : ''}`}
                    id="stateLocation"
                    name="stateLocation"
                    placeholder="State or Location"
                    value={formData.stateLocation}
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
                  {isSubmitting ? 'Submitting...' : 'Get Free Guidance'} <img src={arrowUpRight} alt="Arrow" />
                </button>
              </form>
            </div>
          </div>
        </div>
      </section>

      <section className="container pt-5">
        <h2 className="section-title">Why Parents Contact Us</h2>
        <div className="row">
          <div className="col-12 col-md-3">
            <div className="blue-box">
              <img src={boxIconStranger} alt="Stranger Safety" />
              <p>Concerned about strangers chatting with their child in games.</p>
            </div>
          </div>
          <div className="col-12 col-md-3">
            <div className="blue-box">
              <img src={boxIconInGamePurchase} alt="In-game Purchases" />
              <p>Worried for child about in‑game purchases and scams.</p>
            </div>
          </div>
          <div className="col-12 col-md-3">
            <div className="blue-box">
              <img src={boxIconSafety} alt="Safety Reporting" />
              <p>Unsure how to report unsafe or inappropriate game activity.</p>
            </div>
          </div>
          <div className="col-12 col-md-3">
            <div className="blue-box">
              <img src={boxIconLegal} alt="Legal Steps" />
              <p>Looking for clear, legal steps to protect their child's online safety.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="container pt-5">
        <div className="row align-items-center">
          <div className="col-12 col-md-7">
            <h2 className="section-title">How We Help</h2>
            <ul className="list-text">
              <li>Free confidential consultation with our legal team.</li>
              <li>Step‑by‑step guidance to address gaming safety concerns.</li>
              <li>Support for navigating gaming platform reporting systems.</li>
              <li>Understanding your rights and options as a parent.</li>
            </ul>
          </div>
          <div className="col-12 col-md-5 text-center">
            <img src={imgHowWeHelp} className="img-fluid" alt="How We Help" />
          </div>
        </div>
      </section>

      <section className="container-fluid mt-5 bg-light-blue">
        <div className="container py-4">
          <div className="row">
            <div className="col-12 col-md-3 d-flex justify-content-start align-items-center">
              <h2 className="step-header">Simple 3 Step Process</h2>
              <img src={processArrow} alt="Process Arrow" />
            </div>
            <div className="col-12 col-md-3">
              <div className="stepNo">1</div>
              <h5 className="pt-2">Tell us your concern</h5>
              <p>Fill out the short form given.</p>
            </div>
            <div className="col-12 col-md-3">
              <div className="stepNo">2</div>
              <h5 className="pt-2">We review your situation</h5>
              <p>Our team will assess and guide you.</p>
            </div>
            <div className="col-12 col-md-3">
              <div className="stepNo">3</div>
              <h5 className="pt-2">Take action confidently</h5>
              <p>With our legal and safety guidance.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="container pt-5">
        <div className="row align-items-center">
          <div className="col-12 col-md-5 text-center">
            <img src={imgWhyFamiliesTrustUs} className="img-fluid" alt="Why Families Trust Us" />
          </div>
          <div className="col-12 col-md-7">
            <h2 className="section-title">Why Families Trust Us</h2>
            <ul className="list-text">
              <li>Experienced legal team in digital safety issues.</li>
              <li>Focused on protecting children in online environments.</li>
              <li>Support for navigating gaming platform reporting systems.</li>
              <li>100% confidential & free initial consultation.</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="container bg-child-sefety py-5 mt-5">
        <div className="child-safety-content">
          <h2 className="fw-bold">Your child's safety comes first</h2>
          <p className="mb-0">
            We provide judgment‑free, confidential guidance to help families create a safe online gaming experience.
          </p>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default ParentsPage;
