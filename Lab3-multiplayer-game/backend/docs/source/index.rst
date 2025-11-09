Memory Scramble Game Documentation
===================================

MIT 6.102 Lab 3: Multiplayer Memory Card Game Implementation in Python

Overview
--------

A thread-safe, concurrent multiplayer memory card matching game with:

* **Mutable Board ADT** with representation invariants
* **Space ADT** (immutable, thread-safe)
* **Commands Module** (simple glue code interface)
* **HTTP API** with FastAPI
* **Watch/Event System** for real-time updates
* **Full Test Coverage** with pytest

Getting Started
---------------

1. Install dependencies::

    pip install fastapi uvicorn pytest pytest-asyncio

2. Run tests::

    pytest tests/ -v

3. Start the server::

    python -m src.server

4. Open browser to ``http://localhost:8000``

Core Components
===============

Board ADT
---------

.. automodule:: src.game.board
   :members:
   :undoc-members:
   :show-inheritance:

Space ADT
---------

.. automodule:: src.game.space
   :members:
   :undoc-members:
   :show-inheritance:

Commands Module
---------------

.. automodule:: src.commands.commands.. automodule:: src.commands.com
   :show-inheritance:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
