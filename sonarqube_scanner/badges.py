"""
SonarQube quality gate badges HTML generation.
"""

import logging
import datetime
import requests
from pathlib import Path

logger = logging.getLogger("sonarqube_scanner")


def get_project_badge_token(sonar_url, project_key, auth_token=None):
    """
    Get the badge token for a project from SonarQube API.
    
    Args:
        sonar_url: SonarQube server URL
        project_key: SonarQube project key
        auth_token: SonarQube authentication token
        
    Returns:
        Badge token if available, None otherwise
    """
    try:
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        # Call SonarQube API to get project badge token
        url = f"{sonar_url}/api/project_badges/token?project={project_key}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("token")
        else:
            logger.warning(f"Failed to get badge token for {project_key}: {response.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Error getting badge token for {project_key}: {e}")
        return None


def create_badge_url(sonar_url, project_key, badge_token=None):
    """
    Create a SonarQube quality gate badge URL.
    
    Args:
        sonar_url: SonarQube server URL
        project_key: SonarQube project key
        badge_token: Project-specific badge token
        
    Returns:
        URL for the quality gate badge
    """
    url = f"{sonar_url}/api/project_badges/quality_gate?project={project_key}"
    if badge_token:
        url += f"&token={badge_token}"
    return url


def create_project_url(sonar_url, project_key):
    """
    Create a SonarQube project URL.
    
    Args:
        sonar_url: SonarQube server URL
        project_key: SonarQube project key
        
    Returns:
        URL for the SonarQube project
    """
    return f"{sonar_url}/dashboard?id={project_key}"


def generate_html_content(sonar_url, repositories, auth_token=None):
    """
    Generate HTML content with quality gate badges.
    
    Args:
        sonar_url: SonarQube server URL
        repositories: List of repository configurations
        auth_token: SonarQube authentication token for API calls
        
    Returns:
        HTML content as a string
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>SonarQube Quality Gate Badges</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #0066cc;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }}
        .timestamp {{
            color: #666;
            font-style: italic;
            margin-bottom: 20px;
        }}
        .repositories {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .repository {{
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            width: 100%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .repository h2 {{
            margin-top: 0;
            color: #0066cc;
        }}
        .branches {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .branch {{
            background-color: #f9f9f9;
            border-radius: 5px;
            padding: 10px;
            min-width: 200px;
        }}
        .branch h3 {{
            margin-top: 0;
            font-size: 16px;
            color: #333;
        }}
        a {{
            text-decoration: none;
        }}
        img {{
            max-width: 100%;
        }}
    </style>
</head>
<body>
    <h1>SonarQube Quality Gate Badges</h1>
    <p class="timestamp">Last updated: {timestamp}</p>
    
    <div class="repositories">
"""
    
    # Add repository sections
    for repo in repositories:
        repo_name = repo["name"]
        html += f"""        <div class="repository">
            <h2>{repo_name}</h2>
            <div class="branches">
"""
        
        # Add branch badges
        for branch in repo["branches"]:
            project_key = f"{repo_name}-{branch}".replace("/", "-")
            # Get badge token for this project
            badge_token = get_project_badge_token(sonar_url, project_key, auth_token)
            badge_url = create_badge_url(sonar_url, project_key, badge_token)
            project_url = create_project_url(sonar_url, project_key)
            
            html += f"""                <div class="branch">
                    <h3>{branch}</h3>
                    <a href="{project_url}" target="_blank">
                        <img src="{badge_url}" alt="Quality Gate Status for {repo_name} {branch}" />
                    </a>
                </div>
"""
        
        html += """            </div>
        </div>
"""
    
    html += """    </div>
</body>
</html>
"""
    
    return html


def generate_badges_html(config_data, output_file):
    """
    Generate HTML page with quality gate badges.
    
    Args:
        config_data: Configuration dictionary
        output_file: Output file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        sonar_url = config_data["sonarqube"]["url"]
        sonar_token = config_data["sonarqube"].get("token")
        repositories = config_data["repositories"]
        
        logger.info(f"Generating badges HTML for {len(repositories)} repositories")
        
        # Generate HTML content
        html_content = generate_html_content(sonar_url, repositories, auth_token=sonar_token)
        
        # Write to file
        output_path = Path(output_file)
        output_path.write_text(html_content)
        
        logger.info(f"Badges HTML generated successfully: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error generating badges HTML: {e}")
        return False