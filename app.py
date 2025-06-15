import streamlit as st
import json
from github_analyzer import GitHubRepoAnalyzer, RepoAnalysis
import os

st.set_page_config(
    page_title="AutoReadMe Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 2rem;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.analysis-card {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 10px;
    border-left: 4px solid #667eea;
    margin: 1rem 0;
    color: #333 !important;
}
.analysis-card h3 {
    color: #667eea !important;
    margin-bottom: 1rem;
}
.analysis-card p {
    color: #333 !important;
    margin-bottom: 0.5rem;
    line-height: 1.5;
}
.analysis-card strong {
    color: #495057 !important;
}
.metric-card {
    background: #ffffff;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    text-align: center;
    margin: 0.5rem 0;
}
.success-message {
    background: #d4edda;
    color: #155724 !important;
    padding: 1rem;
    border-radius: 5px;
    border: 1px solid #c3e6cb;
}
.error-message {
    background: #f8d7da;
    color: #721c24 !important;
    padding: 1rem;
    border-radius: 5px;
    border: 1px solid #f5c6cb;
}
[data-testid="metric-container"] {
    background-color: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 1rem;
}
[data-testid="metric-container"] [data-testid="metric-value"] {
    color: #333 !important;
    font-weight: bold;
}
[data-testid="metric-container"] [data-testid="metric-label"] {
    color: #666 !important;
}
.stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
    color: #ffffff !important;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color:#000000;
    border-radius: 4px 4px 0px 0px;
    gap: 8px;
    padding-left: 20px;
    padding-right: 20px;
}
.stTabs [aria-selected="true"] {
    background-color: #667eea;
    color: white;
}
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'github_token' not in st.session_state:
        st.session_state.github_token = ""

def display_analysis_overview(analysis_data: RepoAnalysis):
    st.markdown("### 📊 Quick Overview")
    
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        description = analysis_data.description or 'No description'
        if len(description) > 30:
            description = description[:30] + "..."
        st.metric("📄 Description", description)

    with col2:
        st.metric("🔧 Framework", analysis_data.framework or 'Unknown')

    with col3:
        st.metric("📜 License", analysis_data.license or 'No license')

    with col4:
        topics = analysis_data.topics or []
        topics_str = f"{len(topics)} topics" if topics else 'No topics'
        st.metric("🏷️ Topics", topics_str)

def display_detailed_analysis(analysis: RepoAnalysis):
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "💻 Languages", "📦 Dependencies", "🛠 Setup", "📁 Structure"])
    
    with tab1:
        st.markdown("### 📝 Repository Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Basic Information:**")
            st.write(f"• **Name:** {analysis.name}")
            st.write(f"• **Description:** {analysis.description or 'No description'}")
            st.write(f"• **Primary Language:** {analysis.language or 'Unknown'}")
            st.write(f"• **Framework:** {analysis.framework or 'Not detected'}")
            st.write(f"• **License:** {analysis.license or 'Not specified'}")
            st.write(f"• **Topics:** {', '.join(analysis.topics) if analysis.topics else 'None'}")
        
        with col2:
            st.markdown("**Technical Features:**")
            features = [
                ("Requirements.txt", analysis.has_requirements),
                ("Package.json", analysis.has_package_json),
                ("Setup.py", analysis.has_setup_py),
                ("Makefile", analysis.has_makefile),
                ("Docker", analysis.has_docker),
                ("Tests", analysis.has_tests)
            ]
            for feature, has_feature in features:
                status = "✅ Yes" if has_feature else "❌ No"
                st.write(f"• **{feature}:** {status}")
    
    with tab2:
        st.markdown("### 💻 Programming Languages")
        if analysis.languages:
            total_bytes = sum(analysis.languages.values())
            for lang, bytes_count in sorted(analysis.languages.items(), key=lambda x: x[1], reverse=True):
                percentage = (bytes_count / total_bytes) * 100
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{lang}**")
                with col2:
                    st.write(f"{bytes_count:,} bytes")
                with col3:
                    st.write(f"{percentage:.1f}%")
                st.progress(percentage / 100)
                st.write("")
            try:
                import pandas as pd
                df = pd.DataFrame([
                    {"Language": lang, "Bytes": bytes_count} 
                    for lang, bytes_count in analysis.languages.items()
                ])
                st.bar_chart(data=df.set_index('Language')['Bytes'])
            except ImportError:
                pass
        else:
            st.info("No language data available")
    
    with tab3:
        st.markdown("### 📦 Dependencies")
        if analysis.dependencies:
            for dep_type, deps in analysis.dependencies.items():
                st.markdown(f"#### {dep_type} Dependencies ({len(deps)} packages)")
                if deps:
                    visible_deps = deps[:10]
                    hidden_deps = deps[10:]
                    cols = st.columns(3)
                    for i, dep in enumerate(visible_deps):
                        with cols[i % 3]:
                            st.write(f"• {dep}")
                    if hidden_deps:
                        with st.expander(f"Show {len(hidden_deps)} more dependencies"):
                            cols = st.columns(3)
                            for i, dep in enumerate(hidden_deps):
                                with cols[i % 3]:
                                    st.write(f"• {dep}")
                st.write("")
        else:
            st.info("No dependencies detected")
    
    with tab4:
        st.markdown("### 🛠 Setup Instructions")
        for i, instruction in enumerate(analysis.setup_instructions):
            if instruction.startswith("```"):
                lines = instruction.strip().split('\n')
                if lines[0].startswith("```"):
                    language = lines[0][3:] or "bash"
                    code = '\n'.join(lines[1:-1])
                    st.code(code, language=language)
                else:
                    st.code(instruction.strip("```"), language="bash")
            else:
                st.markdown(instruction)
            if i < len(analysis.setup_instructions) - 1:
                st.markdown("---")
    
    with tab5:
        st.markdown("### 📁 Project Structure")
        if analysis.file_structure:
            def display_tree(structure, level=0, max_items=100):
                items = []
                count = 0
                for name, content in structure.items():
                    if count >= max_items:
                        items.append(f"{'  ' * level}... and more files")
                        break
                    indent = "  " * level
                    if isinstance(content, dict) and 'type' in content:
                        size = content.get('size', 0)
                        if size > 0:
                            size_str = f" ({size//1024}KB)" if size > 1024 else f" ({size}B)"
                        else:
                            size_str = ""
                        items.append(f"{indent}📄 {name}{size_str}")
                    else:
                        items.append(f"{indent}📁 {name}/")
                        if isinstance(content, dict):
                            sub_items = display_tree(content, level + 1, max_items - count)
                            items.extend(sub_items)
                            count += len(sub_items)
                    count += 1
                return items
            
            tree_items = display_tree(analysis.file_structure, max_items=50)
            st.code("\n".join(tree_items), language="")
            
            if len(tree_items) >= 50:
                st.info("Showing first 50 items. Full structure available in exported JSON.")
        else:
            st.info("No file structure data available")

def main():
    initialize_session_state()
    st.markdown('<h1 class="main-header">🚀 AutoReadMe Generator</h1>', unsafe_allow_html=True)
    st.markdown("### Analyze GitHub repositories and generate comprehensive documentation automatically")
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        github_token = st.text_input(
            "GitHub Token",
            value=st.session_state.github_token,
            type="password",
            help="Enter your GitHub personal access token for API access"
        )
        if github_token:
            st.session_state.github_token = github_token
        
        st.markdown("---")
        st.markdown("### 📚 How to use:")
        st.markdown("""
        1. Enter your GitHub token above
        2. Paste a GitHub repository URL
        3. Click 'Analyze Repository'
        4. Review the analysis results
        5. Generate your README
        """)
        
        st.markdown("---")
        st.markdown("### 🔑 GitHub Token:")
        st.markdown("""
        Create a personal access token at:
        [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
        
        Required permissions:
        - repo (for private repos)
        - public_repo (for public repos)
        """)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        repo_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/username/repository",
            help="Enter the full GitHub repository URL"
        )
    with col2:
        st.write("")
        analyze_button = st.button("🔍 Analyze Repository", type="primary", use_container_width=True)
    
    if analyze_button:
        if not st.session_state.github_token:
            st.error("⚠️ Please enter your GitHub token in the sidebar")
        elif not repo_url:
            st.error("⚠️ Please enter a GitHub repository URL")
        else:
            with st.spinner("🔄 Analyzing repository... This may take a few moments"):
                try:
                    analyzer = GitHubRepoAnalyzer(st.session_state.github_token)
                    analysis = analyzer.analyze_repository(repo_url)
                    st.session_state.analysis_result = analysis
                    st.markdown(f"""
                    <div class="success-message">
                        ✅ <strong>Analysis Complete!</strong> Successfully analyzed {analysis.name}
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f"""
                    <div class="error-message">
                        ❌ <strong>Analysis Failed:</strong> {str(e)}
                    </div>
                    """, unsafe_allow_html=True)
    
    if st.session_state.analysis_result:
        analysis = st.session_state.analysis_result
        st.markdown("---")
        st.markdown("## 📊 Analysis Results")
        display_analysis_overview(analysis)
        st.markdown("---")
        display_detailed_analysis(analysis)
        st.markdown("---")
        st.markdown("## 📝 README Generation")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📄 Generate Basic README", use_container_width=True):
                st.info("🚧 README generation feature coming soon!")
        with col2:
            if st.button("📋 Generate Detailed README", use_container_width=True):
                st.info("🚧 Advanced README generation feature coming soon!")
        with col3:
            if st.button("💾 Export Analysis", use_container_width=True):
                analysis_dict = {
                    'name': analysis.name,
                    'description': analysis.description,
                    'language': analysis.language,
                    'languages': analysis.languages,
                    'framework': analysis.framework,
                    'has_docker': analysis.has_docker,
                    'has_requirements': analysis.has_requirements,
                    'has_package_json': analysis.has_package_json,
                    'has_setup_py': analysis.has_setup_py,
                    'has_makefile': analysis.has_makefile,
                    'has_tests': analysis.has_tests,
                    'license': analysis.license,
                    'topics': analysis.topics,
                    'dependencies': analysis.dependencies,
                    'setup_instructions': analysis.setup_instructions
                }
                st.download_button(
                    label="📥 Download Analysis JSON",
                    data=json.dumps(analysis_dict, indent=2),
                    file_name=f"{analysis.name}_analysis.json",
                    mime="application/json"
                )

if __name__ == "__main__":
    main()
