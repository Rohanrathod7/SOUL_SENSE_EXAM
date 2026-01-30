# Common Installation Issues

### Python Version Compatibility

- Soul Sense is tested on **Python 3.11**.
- Newer versions (3.12+) may work but could have dependency conflicts.
- If you encounter issues, try Python 3.11 or check GitHub issues for known problems.

### Dependency Installation Errors

```bash
# Clear pip cache and reinstall
pip cache purge
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Database Initialization Issues

```bash
# Reset database
rm data/soulsense.db
alembic upgrade head
python scripts/setup/seed_questions_v2.py
```

### Permission Errors (Windows)

- Run command prompt as Administrator.
- Or use `pip install --user` for user-level installation.

### Tkinter Missing Error

- **Ubuntu/Debian**: `sudo apt-get install python3-tk`
- **macOS**: Usually included with Python.
- **Windows**: Reinstall Python with the "tcl/tk and IDLE" option enabled.

---

# Runtime Issues

### Application Won't Start

- Check Python version: `python --version`
- Verify virtual environment is activated.
- Check logs in `logs/` directory.

### Database Connection Errors

- Ensure `data/` directory exists and is writable.
- Check file permissions on `soulsense.db`.

### GUI Display Issues

- Set `DISPLAY` environment variable on Linux.
- Try running with `--no-gui` flag for CLI mode (if available).

For more help, check the [User Manual](docs/USER_MANUAL.md) or open an issue on GitHub.
