import streamlit as st

def init_page_config():
    """Initialize page configuration"""
    if not st._is_running_with_streamlit:
        return
        
    st.set_page_config(
        page_title="Math Learning App",
        page_icon="✏️",
        layout="centered",
        initial_sidebar_state="expanded"
    )

def init_latex_support():
    """Initialize LaTeX and MathJax support"""
    # Add MathJax scripts and configuration
    st.markdown("""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.9/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>
        <script>
            MathJax.Hub.Config({
                tex2jax: {
                    inlineMath: [['$','$']],
                    displayMath: [['$$','$$']],
                    processEscapes: true,
                    processEnvironments: true,
                    skipTags: ['script', 'noscript', 'style', 'textarea', 'pre'],
                    TeX: {
                        equationNumbers: { autoNumber: "AMS" },
                        extensions: ["AMSmath.js", "AMSsymbols.js"]
                    }
                },
                messageStyle: "none",
                styles: {
                    ".MathJax": {
                        "font-size": "115%"
                    }
                },
                displayAlign: "left"
            });
        </script>
    """, unsafe_allow_html=True)

def init_styles():
    """Initialize custom CSS styles"""
    st.markdown("""
        <style>
            /* General text styles */
            .question-text {
                font-size: 1.2em;
                margin: 1em 0;
                line-height: 1.5;
            }
            
            /* LaTeX/Math rendering styles */
            .math-display {
                font-size: 1.1em;
                margin: 12px 0;
                padding: 8px 0;
            }
            
            /* Radio button option styles */
            .stRadio [role=radiogroup] {
                font-size: 1.1em;
                margin: 1em 0;
            }
            .stRadio [role=radiogroup] label {
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                margin: 5px 0;
            }
            .stRadio [role=radiogroup] label:hover {
                background-color: #e9ecef;
            }
            
            /* Solution text styles */
            .solution-text {
                font-size: 1.1em;
                margin-top: 1.5em;
                padding: 15px;
                background-color: #f8f9fa;
                border-left: 4px solid #28a745;
                border-radius: 4px;
            }
            
            /* Error message styles */
            .error-text {
                color: #dc3545;
                font-weight: bold;
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
            }
            
            /* Success message styles */
            .success-text {
                color: #28a745;
                font-weight: bold;
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
            }
        </style>
    """, unsafe_allow_html=True)

# LaTeX configuration constants
LATEX_CONFIG = {
    'inline_delimiters': ['$', '$'],
    'display_delimiters': ['$$', '$$'],
    'enable_numbering': False,
    'font_size': '115%'
}

def init_app(skip_page_config=False):
    """Initialize all app configurations"""
    if not skip_page_config:
        init_page_config()
    init_latex_support()
    init_styles()