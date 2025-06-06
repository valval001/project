pipeline {
    agent any

    environment {
        SONARQUBE = 'MySonarQube'
        SONAR_TOKEN = credentials('sonar-token')
        FLASK_SECRET_KEY = credentials('flask-secret')
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        IMAGE_TAG = "${BUILD_NUMBER}"
        IMAGE_NAME = "ditisspriyanshu/jenkins:${BUILD_NUMBER}"
        DEPENDENCY_CHECK_HOME = tool 'OWASP'
        GIT_CRED_ID = 'git-token'
    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/valval001/project.git', branch: 'dev'
            }
        }

        stage('Bandit Security Scan') {
            steps {
                sh '''
                    echo "Running Bandit security scan..."
                    export PATH=$PATH:/var/lib/jenkins/.local/bin
                    bandit -r . -f html -o bandit-report.html -f sarif -o bandit-report.sarif || true
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'bandit-report.*', fingerprint: true
                    recordIssues enabledForFailure: true, tools: [sarif(pattern: 'bandit-report.sarif')]
                    publishHTML(target: [
                        reportName: 'Bandit Report',
                        reportDir: '.',
                        reportFiles: 'bandit-report.html',
                        keepAll: true
                    ])
                }
            }
        }

        stage('OWASP Dependency Check') {
            steps {
                sh '''
                    echo "Running OWASP Dependency Check..."
                    mkdir -p dependency-check-report
                    $DEPENDENCY_CHECK_HOME/bin/dependency-check.sh \
                    --project "MyProject" \
                    --scan . \
                    --format ALL \
                    --out dependency-check-report
                '''
            }
            post {
                always {
                    dependencyCheckPublisher(
                        failedTotalCritical: 0,
                        unstableTotalHigh: 5,
                        unstableTotalMedium: 10,
                        failedNewCritical: 0,
                        unstableNewHigh: 5,
                        unstableNewMedium: 10
                    )
                    archiveArtifacts artifacts: 'dependency-check-report/dependency-check-report.*', fingerprint: true
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv(SONARQUBE) {
                    sh """
                        echo $FLASK_SECRET_KEY > /dev/null
                        sonar-scanner -Dsonar.login=${SONAR_TOKEN}
                    """
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Trivy Dockerfile Scan') {
            steps {
                sh '''
                    echo "Scanning Dockerfile for misconfigurations..."
                    trivy config --format table --output trivy-dockerfile-report.html Dockerfile || true
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-dockerfile-report.html', fingerprint: true
                    publishHTML(target: [
                        reportName: 'Trivy Dockerfile Report',
                        reportDir: '.',
                        reportFiles: 'trivy-dockerfile-report.html',
                        keepAll: true
                    ])
                }
            }
        }

        stage('SBOM - Source') {
            steps {
                sh '/var/lib/jenkins/bin/syft dir:. -o cyclonedx-json > sbom-source.json'
                archiveArtifacts artifacts: 'sbom-source.json', fingerprint: true
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh "docker build -t ${IMAGE_NAME} ."
                }
            }
        }

        stage('SBOM - Image') {
            steps {
                sh '''
                    /var/lib/jenkins/bin/syft ${IMAGE_NAME} -o cyclonedx-json > sbom-image.json
                '''
                archiveArtifacts artifacts: 'sbom-image.json', fingerprint: true
            }
        }

        stage('Upload SBOM to Dependency-Track') {
            steps {
                dependencyTrackPublisher artifact: 'sbom-image.json',
                    projectName: 'ecommerce-image',
                    projectVersion: "${IMAGE_TAG}",
                    synchronous: true
            }
        }

        stage('Trivy Image Scan') {
            steps {
                sh '''
                    echo "Scanning Docker image for vulnerabilities..."
                    export TRIVY_DISABLE_VEX_NOTICE=true
                    trivy image --ignore-unfixed --exit-code 1 --severity CRITICAL ${IMAGE_NAME} > trivy-image-report.txt || true
                    cat trivy-image-report.txt

                    if grep -q "CRITICAL" trivy-image-report.txt; then
                        echo "Critical vulnerabilities found in Docker image."
                        docker rmi ${IMAGE_NAME}
                        exit 1
                    fi
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-image-report.*', fingerprint: true
                    recordIssues enabledForFailure: true, tools: [trivy(pattern: 'trivy-image-report.txt')]
                    publishHTML(target: [
                        reportName: 'Trivy Image Report',
                        reportDir: '.',
                        reportFiles: 'trivy-image-report.txt',
                        keepAll: true
                    ])
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    sh """
                        echo "${DOCKERHUB_CREDENTIALS_PSW}" | docker login -u "${DOCKERHUB_CREDENTIALS_USR}" --password-stdin
                        docker push ${IMAGE_NAME}
                        docker logout
                        docker rmi ${IMAGE_NAME}
                    """
                }
            }
        }

        stage('Merge to Master and Update Deployment') {
            steps {
                withCredentials([usernamePassword(credentialsId: "${env.GIT_CRED_ID}", usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')]) {
                    sh """
                        git config user.name "Jenkins CI"
                        git config user.email "jenkins@example.com"

                        git remote set-url origin https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/valval001/project.git

                        # Fetch and checkout master
                        git fetch origin master
                        git checkout master

                        # Merge dev into master
                        git merge origin/dev --no-edit

                        # Update image tag in deployment.yml on master branch
                        sed -i "s|image: ditisspriyanshu/jenkins:.*|image: ditisspriyanshu/jenkins:${BUILD_NUMBER}|" kubernetes/deployment.yml

                        git add kubernetes/deployment.yml
                        git commit -m "${BUILD_NUMBER}"
                        git push origin master
                    """
                }
            }
        }

    }

    post {
        success {
            mail to: 'priyanshuagarwal801@gmail.com',
                subject: "✅ Jenkins Build Passed - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Good news! Build #${env.BUILD_NUMBER} succeeded.\n\nCheck: ${env.BUILD_URL}"
        }
        failure {
            mail to: 'priyanshuagarwal801@gmail.com',
                subject: "❌ Jenkins Build Failed - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Oops! Build #${env.BUILD_NUMBER} failed.\n\nCheck: ${env.BUILD_URL}"
        }
        always {
            cleanWs()
        }
    }
}
