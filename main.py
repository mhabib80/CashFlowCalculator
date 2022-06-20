from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect
import tempfile
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plt_params
from matplotlib import ticker
import io
import base64


app = Flask(__name__)
app.config['SECRET_KEY'] = 'ljyhfjfkjfjfou7867856'
Bootstrap(app)
csrf = CSRFProtect(app)

# tmp = os.environ.get('tmp')


def sigmoid(x, k=3.627412246682911, b=-0.001164921989173435):
    return 1 / (1 + np.exp(-k*(x-b)))


def curve(p_name, contract_amount, start_date, completion_date,  curve, csrf=None):
    date_range = pd.date_range(start_date, completion_date, freq='d')  # date range per day
    dur = (date_range.max() - date_range.min()).days
    if curve == 'trapezoidal':
        sigmoid_input = np.linspace(-1.1, 1.1, dur + 1) #adjust the x values to better fit the S-Curve function
        x = sigmoid(sigmoid_input)
    else:
        x = np.linspace(0, 1, dur + 1)
    cum_earnings = (x * contract_amount).ravel()
    data = pd.DataFrame(cum_earnings, index=date_range, columns=['cum_earnings'])
    data.iloc[0] = 0
    # data.iloc[-1] = contract_amount  # last period should be 100% contract amount
    output = data.resample('M').cum_earnings.max().astype(int).to_frame()
    output[p_name + '_Monthly'] = output['cum_earnings'].diff().fillna(output['cum_earnings']) #so 1st period won't be NaN
    output.drop('cum_earnings', inplace=True, axis=1)
    return output


def plot_chart():

    df = pd.read_csv('/tmp/df.csv', index_col=[0])
    ax = df.iloc[:, :-2].plot(kind='bar', stacked=True, figsize=(20, 15),
                              color=['#06283D', '#1363DF', '#47B5FF', '#FF6D02', '#7577CD'])
    ax2 = df['Cum_Monthly'].plot(c='red', ax=ax, secondary_y=True, legend=True, label='Cum_Monthly')
    ax.legend(loc='upper left', frameon=False, ncol=len(df.columns))
    ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax2.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    img = io.BytesIO()
    plt.savefig(img, format = 'png')
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(img.getvalue()).decode('utf8')
    return pngImageB64String



# Create Forms
def validate_date(form, field):
    if form.project_end.data < form.project_start.data:
        raise ValidationError('Project end date must be greater than start date')


class SingleProject(FlaskForm):
    project_name = StringField('Project Name',  validators=[DataRequired()])
    project_value = IntegerField('Project Value',  validators=[DataRequired()])
    project_start = DateField('Project Start Date', validators=[DataRequired()])
    project_end = DateField('Project End Date', validators=[DataRequired(), validate_date])
    distribution = SelectField('Curve Type', choices=[('linear', 'Linear'), ('trapezoidal', 'Trapezoidal(S-Curve)')],
                               validators=[DataRequired()])
    # delete = SubmitField('Remove Project')


class Projects(FlaskForm):
    projects = FieldList(FormField(SingleProject), min_entries=1)
    submit = SubmitField('Enter')
    add = SubmitField('Add a Project')
    restart = SubmitField('Restart Form')


project_dfs = {}


@app.route('/', methods=['POST', 'GET'])
def home():
    table = None
    img = None
    form = Projects(request.form)
    if request.form.get('add'):
        form.projects.append_entry()
    if request.form.get('restart'):
        form = Projects()
        return redirect(url_for('home'))
    # if request.form.get('delete'):
    #     print(request.form.to_dict())
    if request.method == 'POST':
        if form.validate_on_submit():
            for project in form.projects.data:
                # Each project in form.projects.data is a dictionary.
                # Output a dataframe with each project's monthly (incremental) values
                df = curve(*project.values())
                name = project.get('project_name')
                # add the project to the dictionary project_dfs
                project_dfs[name] = df
            # combine and process all dataframes in the projects_dfs
            table_df = pd.concat(project_dfs.values(), axis=1).fillna(0).assign(Monthly_Total = lambda x : x.sum(1))
            table_df['Cum_Monthly'] = table_df['Monthly_Total'].cumsum()
            table_df.to_csv('/tmp/df.csv')
            img = plot_chart()
            # process the combined dataframe to html
            table = table_df.applymap(lambda x: f'${x:,.0f}')\
                .to_html(classes='table table-striped borderless', justify='left')

        else:
            for k,v in form.errors['projects'][0].items():
                flash(f'{k}: {v[0]}')

    return render_template('index.html', form = form, table=table, img = img)


@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory('/tmp', filename)



if __name__ == '__main__':
    app.run(debug=True)
