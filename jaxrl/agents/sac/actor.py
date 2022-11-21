from typing import Tuple, Optional

import jax
import jax.numpy as jnp

from jaxrl.datasets import Batch
from jaxrl.networks.common import InfoDict, Model, Params, PRNGKey


def update(key: PRNGKey, actor: Model, critic: Model, temp: Model,
           batch: Batch) -> Tuple[Model, InfoDict]:

    def actor_loss_fn(actor_params: Params) -> Tuple[jnp.ndarray, InfoDict]:
        dist = actor.apply_fn({'params': actor_params}, batch.observations)
        actions = dist.sample(seed=key)
        log_probs = dist.log_prob(actions)
        q1, q2 = critic(batch.observations, actions)
        q = jnp.minimum(q1, q2)
        actor_loss = (log_probs * temp() - q).mean()
        return actor_loss, {
            'sac_pi_loss': actor_loss,
            'entropy': -log_probs.mean(),
            'L1_codes': jnp.sum(jnp.abs(actor_params['codes'])),
            'L1_components': jnp.sum(jnp.abs(actor_params['components']))
        }

    new_actor, info = actor.apply_gradient(actor_loss_fn)

    return new_actor, info