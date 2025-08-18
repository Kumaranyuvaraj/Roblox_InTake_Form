import React from 'react';
import { useNavigate } from 'react-router-dom';

const SuccessModal = ({ show, onHide, message = "Your request has been submitted successfully." }) => {
  const navigate = useNavigate();

  const handleOkClick = () => {
    onHide();
    navigate('/thank-you');
  };

  if (!show) return null;

  return (
    <div className={`modal fade ${show ? 'show' : ''}`} style={{ display: show ? 'block' : 'none' }} tabIndex="-1" aria-labelledby="successModalLabel" aria-hidden={!show}>
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content text-center">
          <div className="modal-header border-0">
            <h5 className="modal-title w-100" id="successModalLabel">Thank You!</h5>
          </div>
          <div className="modal-body">
            {message}
          </div>
          <div className="modal-footer justify-content-center border-0">
            <button type="button" className="btn btn-primary" onClick={handleOkClick}>
              OK
            </button>
          </div>
        </div>
      </div>
      <div className="modal-backdrop fade show" onClick={onHide}></div>
    </div>
  );
};

export default SuccessModal;
