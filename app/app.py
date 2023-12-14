import plotly.utils
from flask import Flask,render_template,redirect,flash,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from wtforms import StringField,SubmitField,PasswordField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, current_user,logout_user, login_required

import numpy as np
import pandas as pd

from nsepy import get_history
from datetime import date

import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import json

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///stockpred.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']='f4e3661b9412ffeed8bea85cb716ad3c'
db= SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view='login'
login_manager.login_message_category='info'



@login_manager.user_loader
def load_user(id):
# Here we tell flask-login to identify our user with the help of ID from our registration model
    return Registration.query.get(int(id))

#Models
class Registration(db.Model,UserMixin):
    #UserMixin provides a common interface that any user model needs to implement to work with Flask-Login.
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20),unique=True, nullable=False)
    name = db.Column(db.String(30),nullable=False)
    email= db.Column(db.String(30),nullable=False,unique=True)
    password= db.Column(db.String(25),nullable=False)
    time= db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self)-> str:
        return f'{self.username}-{self.name}-{self.email}'


class Login(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20),nullable=False)
    password= db.Column(db.String(25),nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self)-> str:
        return f'{self.username}'



#Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=5, max=20)])
    name= StringField('Username',
                           validators=[DataRequired(), Length(min=5, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password',message="Passwords must match!")])
    submit = SubmitField('Sign up')

    def validate_username(self,username):
        user= Registration.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username already exits.')


    def validate_email(self,email):
        user= Registration.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already registered.')



class LoginForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')




@app.route('/')
def home():
    #pandas dataframe
    nifty = get_history(symbol="NIFTY 50",
                        start=date(2000, 1, 1), end=date.today(),
                        index=True)
    nifty.reset_index('Date', inplace=True)
    nifty.drop(['Turnover'], axis=1, inplace=True)
    nifty_tail = nifty.tail(10)

    label = ['RIL', 'HDFC BANK', 'INFOSYS', 'ICICI BANK', 'HDFC', 'TCS', 'KOTAK MAHINDRA BANK',
              'L&T', 'HUL', 'ITC', 'BAJAJ FINANCE', 'SBI', 'BHARTI AIRTEL', 'AXIS BANK', 'ASIAN PAINTS',
              'HCL TECH','BAJAJ FINSERV', 'TITAN', 'TECH MAHINDRA', 'MARUTI SUZUKI INDIA', 'WIPRO', 'UTRATECH CEMENT',
              'TATA STEEL','TATA MOTORS', 'SUN PHARMA', 'M&M', 'POWER GRID', 'NESTLE INDIA', 'GRASIM INDUSTRIES',
              'HDFC LIFE INSURANCE', "DIVI'S LAB",'HINDALCO INDUSTRIES', 'JSW STEEL', 'NTPC', "DR REDDY'S LABS", 'INDUSLND BANK', 'ONGC',
              'SBI LIFE INSURANCE','ADANI PORTS', 'CIPLA', 'TATA CONSUMER PRODUCTS', 'BAJAJ AUTO', 'BRITANNIA INDUSTRIES', 'UPL', 'BPCL',
              'SHREE CEMENTS','EICHER MOTORS', 'COAL INDIA', 'HERO MOTOCORP', 'IOC']

    value = [10.56, 8.87, 8.62, 6.72, 6.55, 4.96, 3.91, 2.89, 2.81, 2.63, 2.52, 2.40, 2.33,
              2.29, 1.92, 1.68, 1.41,1.35, 1.30, 1.28, 1.28, 1.17, 1.14,1.12, 1.1, 1.09, 0.96,
              0.93, 0.86, 0.86, 0.84, 0.82, 0.82, 0.82, 0.77, 0.72, 0.7, 0.69, 0.68, 0.67, 0.63,
              0.57, 0.57, 0.51, 0.48, 0.47, 0.45,0.43, 0.43, 0.41]

    data = {
        'labels': label,
        'values': value,
    }

    df = pd.DataFrame(data)

    fig = px.pie(df, values='values', names='labels', labels={'labels': 'Stock', 'values': 'WEIGHTAGE'})
    fig.update_traces(textposition='inside')
    fig.update_layout(paper_bgcolor='#F8F9FA',uniformtext_minsize=12, uniformtext_mode='hide',
                      title_text='OVERVIEW OF STOCKS IN NIFTY50',title_x=0.27)


    graphJSON =json.dumps(fig,cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('home.html',graphJSON=graphJSON,tables=[nifty_tail.to_html(classes='nifty',index=False)],
                           titles=['Nifty50 of last 10 trading sessions'])



@app.route('/search')
@login_required
def search():
    return render_template('search.html')

@app.route('/stock_analysis')
def stock_analysis():
    return render_template('stock_analysis.html')

@app.route('/signup',methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form=RegistrationForm()

    if form.validate_on_submit(): #on form submission
        #Here we hash the password entered by the user
        hashed_password= bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        #Here we collect the details, the user has filled in the form
        registered_user =  Registration(username=form.username.data, email=form.email.data,
                                        name= form.name.data ,password=hashed_password)
        #Here we add those details into the database
        db.session.add(registered_user)
        db.session.commit()
        #Here we display the flash message and redirect user to the login page
        flash("You have registered succesfully !" ,'success')
        return redirect(url_for('login'))
    return render_template('signup.html',title='Register',form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form=LoginForm()
    if form.validate_on_submit(): #on form submission
    #Firstly we will the check if the username entered in the login form is registered from the registration model

        user= Registration.query.filter_by(username=form.username.data).first()

    #If it exists and the password entered by user is same as the hashed password used while registration
    # Then the user is logged in and is redirected to home page

        if user and bcrypt.check_password_hash(user.password,form.password.data):
            logged_in_user=Login(username=form.username.data, password = user.password)
            db.session.add(logged_in_user)
            db.session.commit()

            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Please check your email and password.",'danger')
    return render_template('login.html',title='Login',form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/search/wipro")
@login_required
def wipro():
    wipro = get_history(symbol="WIPRO",
                              start=date(2000, 1, 1),
                              end=date.today())
    wipro = wipro.tail(15)
    wipro.drop(['Symbol', 'Series', 'Turnover', '%Deliverble', 'Trades', 'Deliverable Volume'], axis=1, inplace=True)
    wipro.reset_index(inplace=True)


    return render_template("wipro.html",tables=[wipro.to_html(classes='wipro',index=False)],
                           titles=["Wipro's performance over last 15 trading sessions"])



if __name__ == '__main__':
    app.run(debug=True)

