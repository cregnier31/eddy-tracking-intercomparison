pipeline {

    agent { label 'bengale' }
    

    options {
        skipDefaultCheckout(true)
        parallelsAlwaysFailFast()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '3'))
    }

    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
                script {
                    def result = sh (script: "git log -1 | grep '.*\\[ci skip\\].*'", returnStatus: true)
                    echo "${result}"
                    if (result == 0) {
                        currentBuild.result = 'ABORTED'
                        error("ci skip found in last commit. Aborting build.")
                    }
                }
            }
        }

        stage('PyPI Package and Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh """#!/bin/bash
                . ~/.bashrc
                set -e

                conda activate hatch_cicd

                echo " *** Bump version"
                hatch version minor

                echo " *** Build package"
                hatch build --clean

                echo "*** Deploy package"
		hatch publish -r pypi-internal

                echo "*** Commit changes"
		git push git@gitlab.mercator-ocean.fr:/internal-shared-group/validation/eddy-tracking-intercomparison.git HEAD:master
                git push git@gitlab.mercator-ocean.fr:/internal-shared-group/validation/eddy-tracking-intercomparison.git --tags
                """
            }
        }
    }

    post{
        changed {
            emailext to: "scailleau@mercator-ocean.fr",
            subject: "Jenkins build:${currentBuild.currentResult}: ${env.JOB_NAME}",
            body: "${currentBuild.currentResult}: Job ${env.JOB_NAME}\nMore Info can be found here: ${env.BUILD_URL}",
            attachLog: true
        }
    }
}
