"""Netlify build step script.

Copies static assets into the public directory for fast CDN delivery by Netlify.
"""
import os
import shutil

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(root_dir, "static")
    public_dir = os.path.join(root_dir, "public")
    public_static_dir = os.path.join(public_dir, "static")

    print("[BUILD] Preparing Netlify static distribution directory...")
    os.makedirs(public_dir, exist_ok=True)
    if os.path.exists(static_dir):
        if os.path.exists(public_static_dir):
            shutil.rmtree(public_static_dir)
        shutil.copytree(static_dir, public_static_dir)
        print(f"[BUILD] Successfully copied {static_dir} to {public_static_dir}")
    print("[BUILD] Netlify build preparation complete.")

if __name__ == "__main__":
    main()
