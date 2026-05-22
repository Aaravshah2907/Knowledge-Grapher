---
id: ito-lemma
title: Itô's Lemma
tags: [stochastic-calculus, sde]
depends_on: [brownian-motion, stochastic-integral]
---
# Itô's Lemma

The fundamental chain rule for Itô processes. If $X_t$ solves
$dX_t = \mu_t\,dt + \sigma_t\,dW_t$, then for smooth $f$:

$$df(t, X_t) = \frac{\partial f}{\partial t}\,dt + \frac{\partial f}{\partial x}\,dX_t + \frac{1}{2}\frac{\partial^2 f}{\partial x^2}\,d[X]_t$$

Depends conceptually on [[brownian-motion]] and [[stochastic-integral]].
