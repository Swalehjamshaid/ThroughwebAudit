# ... inside register() route ...
        db.session.add(new_user)
        try:
            db.session.commit()
            # NOW CALL THE UTILITY FUNCTION
            from .utils import send_verification_email
            send_verification_email(new_user) 
            
            flash('Registration successful! Please check your email for a verification link.', 'info')
            return redirect(url_for('auth.login'))
        except Exception:
            # Handle database error if commit fails (e.g., integrity constraint)
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('auth.register'))
        # ... end of block ...
