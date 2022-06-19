import pandas as pd
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect
from functions import *


app = Flask(__name__)
app.config['SECRET_KEY'] = 'ljyhfjfkjfjfou7867856'
Bootstrap(app)
csrf = CSRFProtect(app)

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
            table_df.to_csv('static/files/df.csv')
            plot_chart()

            # process the combined dataframe to html
            table = table_df.applymap(lambda x: f'${x:,.0f}')\
                .to_html(classes='table table-striped borderless', justify='left')
        else:
            print(form.errors)
            # print(form.errors['projects'][0])
            for k,v in form.errors['projects'][0].items():
                flash(f'{k}: {v[0]}')


    return render_template('index.html', form = form, table=table)





@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory('static/files', filename)



if __name__ == '__main__':
    app.run(debug=True)
