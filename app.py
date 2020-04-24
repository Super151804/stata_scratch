import os
from os import path
import shutil
import pickle
from flask import Flask, request, render_template, redirect
from werkzeug.utils import secure_filename
import pandas as pd
from sourceCode import linear_reg
from sourceCode.func import get_corr, gethtml

app = Flask(__name__)
commandList = ["linear_reg"]
session = {}


@app.route("/", methods=['GET', 'POST'])
def passwd():
    """
    login page
    """
    try:
        """if redirected from /"""
        name = request.form["username"]
        passwd = request.form["passwd"]
        try:
            with open("users_info.pickle", "rb") as f:
                data = pickle.load(f)
        except FileNotFoundError:
            with open("users_info.pickle", "wb") as f:
                data = {'admin': 'admin'}
                pickle.dump(data, f)
        if name not in data:
            """if not registered"""
            return render_template("login.html", script="alert('Not Registered!')")
        if data[name] != passwd:
            """if password is wrong"""
            return render_template("login.html", script="alert('Wrong Password!')")
        """if all is well"""
        session["username"] = name
        if os.path.exists("./static/" + name):
            shutil.rmtree("./static/" + name)
        return redirect("data")
    except:
        """if redirected from register"""
        try:
            name = request.form["addUser"]
            passwd = request.form["addpwd"]
            with open("users_info.pickle", "rb") as f:
                data = pickle.load(f)
            if name in data:
                """if username exists"""
                return render_template("login.html", script="alert('name is registered!Try another name.')")
            data[name] = passwd
            with open("users_info.pickle", "wb") as f:
                pickle.dump(data, f)
            return render_template("login.html", script="alert('registered!')")
        except:
            """if user just clicks the button"""
            return render_template("login.html", scipt="alert('Input')")


@app.route("/data", methods=['GET', 'POST'])
def upload():
    """
    upload file to ./static/username/uploads/*
    write the filename into ./static/username/loadfile.txt
    jump to upload page to preview data and choose method
    """
    try:
        name = session["username"]
        if not os.path.exists("./static/" + name):
            os.mkdir("./static/" + name)
            os.mkdir("./static/{}/uploads".format(name))
            os.mkdir("./static/{}/downloads".format(name))
        if request.method == 'POST':
            f = request.files["file"]
            base_path = path.abspath(path.dirname(__file__))
            upload_path = path.join(base_path, 'static/{}/uploads/'.format(name))
            file_name = upload_path + secure_filename(f.filename)
            uploadFileName = open("./static/{}/loadfile.txt".format(name), "a", encoding="utf-8")
            print(file_name, file=uploadFileName)
            uploadFileName.close()
            f.save(file_name)
            return redirect("check")
        return render_template('upload.html')
    except Exception:
        return redirect("error")


@app.route("/check", methods=['GET', 'POST'])
def checkResult():
    """
    show about 20 lines of data
    clean data
    """
    try:
        name = session["username"]
        with open("./static/{}/loadfile.txt".format(name)) as f:
            filename = f.readlines()[-1][:-1]
        uploadFile = open(filename, "r", encoding="utf-8")
        fileinfo = uploadFile.readlines()[:20]
        fileinfo = gethtml(fileinfo)
        uploadFile.close()
        return render_template("show.html", file=fileinfo)
    except Exception:
        return redirect("error")


@app.route("/upload", methods=['GET', 'POST'])
def showResult():
    """
    show corr
    let user to choose command, dependent variable
    """
    try:
        name = session["username"]
        nullMethod = request.form["isnull"]
        with open("./static/{}/loadfile.txt".format(name)) as f:
            filename = f.readlines()[-1][:-1]
        data = pd.read_csv(filename)
        if nullMethod[0] == "d":
            data = data.dropna()
        else:
            data = data.fillna(0)
        commandStr = "<h2>the corr matrix is</h2>" + get_corr(data)
        data.to_csv(filename, encoding="utf-8")
        commandStr += "<h2>please choose your command</h2>"
        title = list(data.columns)
        for i in commandList:
            commandStr += "<input type='radio' value='{}' name='command'>{}<br>".format(i, i)
        commandStr += "<br><h2>please choose your dependent variable</h2>"
        for i in title:
            commandStr += "<input type='radio' value='{}' name='dependent'>{}<br>".format(i, i)
        commandStr += "<br><h2>please choose your independent variable(s)</h2>"
        for i in title:
            commandStr += "<input type='checkbox' value='{}' name='independent'>{}<br>".format(i, i)
        return render_template("clean.html", command=commandStr)
    except ValueError:
        return redirect("VE")
    except Exception:
        return redirect("error")


@app.route("/result", methods=['GET', 'POST'])
def show():
    """TODO: if it's dummy but user uses linear_reg"""
    """
    show the result
    """
    name = session["username"]
    with open("./static/{}/loadfile.txt".format(name)) as f:
        filename = f.readlines()[-1][:-1]
    wfile = open("./static/{}/commandhis.txt".format(name), "a", encoding="utf-8")
    tmp = request.form["command"]
    dependentVariable = request.form["dependent"]
    independentVariable = request.form.getlist("independent")
    independentVariable[-1] = independentVariable[-1]
    varFiles = open("./static/{}/var.txt".format(name), "a", encoding="utf-8")
    print(dependentVariable, '\t', independentVariable, file=varFiles)
    varFiles.close()
    ans = eval(tmp + ".getAns('{}',{},'{}')".format(dependentVariable, independentVariable, name))
    gdnfile = eval(tmp + ".showAns('{}',{},'{}')".format(dependentVariable, ans, name))
    print(tmp, file=wfile)
    wfile.close()
    rfile = open("./static/{}/commandhis.txt".format(name), "r", encoding="utf-8")
    content = rfile.read().replace('\n', '<br>')
    rfile.close()
    tfigure = eval(tmp + ".create_t_figure({})".format(ans))
    bfigure = eval(tmp + ".create_b_figure({})".format(ans))
    pfigure = eval(tmp + ".create_p_figure({})".format(ans))
    return """<html>
                <head>
                    <title>ans</title>
                </head>
                <body>
                    <h1>datainfo</h1>
                    <p>{}</p>
                    <img src="{}"><br>
                    <img src="{}"><br>
                    <img src="{}"><br>
                    <a href="/datainfo">Click to Download the Result</a>
                    <h2>command history</h2>
                    <p>{}</p>
                    <a href="/check">preview again</a>
                    <a href="./static/{}/uploads/{}>download your raw data</a>
                </body>
                </html>
            """.format(gdnfile, tfigure, bfigure, pfigure, content, name, filename)


@app.route("/datainfo")
def forDownloads():
    name = session["username"]
    return redirect("/static/{}/downloads/ans.csv".format(name))


@app.route("/error")
def cerr():
    html = """
        <!DOCTYPE html>
        <html lang="zh">
          <head>
            <meta charset="UTF-8" />
            <title>Title</title>
          </head>
          <body>
          <script>
          alert("Please Check Your Data Or Login")
          </script>
            <a href="/">return to login page</a>
          </body>
        </html>
    """
    return html


@app.route("/VE")
def valerr():
    html = """
        <!DOCTYPE html>
        <html lang="zh">
          <head>
            <meta charset="UTF-8" />
            <title>Title</title>
          </head>
          <body>
          <script>
          alert("Is it dummy?")
          </script>
            <a href="/check">return to check page</a>
          </body>
        </html>
    """
    return html


if __name__ == "__main__":
    app.run(thread=True)
