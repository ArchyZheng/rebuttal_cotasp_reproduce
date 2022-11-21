from typing import List
import random
import gym
import metaworld
import numpy as np
from gym.wrappers import TimeLimit

from jaxrl import wrappers

def get_mt50() -> metaworld.MT50:
    saved_random_state = np.random.get_state()
    np.random.seed(999)
    random.seed(999)
    MT50 = metaworld.MT50()
    np.random.set_state(saved_random_state)
    return MT50

TASK_SEQS = {
    "cw10": [
        "hammer-v1",
        "push-wall-v1",
        "faucet-close-v1",
        "push-back-v1",
        "stick-pull-v1",
        "handle-press-side-v1",
        "push-v1",
        "shelf-place-v1",
        "window-close-v1",
        "peg-unplug-side-v1",
    ],
    "cw1-hammer": [
        "hammer-v1"
    ],
    "cw1-push-back": [
        "push-back-v1"
    ],
    "cw1-push": [
        "push-v1"
    ],
    "cw2-test": [
        "hammer-v1",
        "stick-pull-v1",
    ],
    "cw3-test": [
        "hammer-v1",
        "stick-pull-v1",
        "push-back-v1"
    ]
}

TASK_SEQS["cw20"] = TASK_SEQS["cw10"] + TASK_SEQS["cw10"]
META_WORLD_TIME_HORIZON = 200
MT50 = get_mt50()

class RandomizationWrapper(gym.Wrapper):
    """Manages randomization settings in MetaWorld environments."""

    ALLOWED_KINDS = [
        "deterministic",
        "random_init_all",
        "random_init_fixed20",
        "random_init_small_box",
    ]

    def __init__(self, env: gym.Env, subtasks: List[metaworld.Task], kind: str) -> None:
        assert kind in RandomizationWrapper.ALLOWED_KINDS
        super().__init__(env)
        self.subtasks = subtasks
        self.kind = kind

        env.set_task(subtasks[0])
        if kind == "random_init_all":
            env._freeze_rand_vec = False

        if kind == "random_init_fixed20":
            assert len(subtasks) >= 20

        if kind == "random_init_small_box":
            diff = env._random_reset_space.high - env._random_reset_space.low
            self.reset_space_low = env._random_reset_space.low + 0.45 * diff
            self.reset_space_high = env._random_reset_space.low + 0.55 * diff

    def reset(self, **kwargs) -> np.ndarray:
        if self.kind == "random_init_fixed20":
            self.env.set_task(self.subtasks[random.randint(0, 19)])
        elif self.kind == "random_init_small_box":
            rand_vec = np.random.uniform(
                self.reset_space_low, self.reset_space_high, size=self.reset_space_low.size
            )
            self.env._last_rand_vec = rand_vec

        return self.env.reset(**kwargs)


def get_subtasks(name: str) -> List[metaworld.Task]:
    return [s for s in MT50.train_tasks if s.env_name == name]


def get_single_env(
    name, seed, 
    randomization="random_init_all",
    add_episode_monitor=True
):
    if name == "HalfCheetah-v3" or name == "Ant-v3":
        env = gym.make(name)
        env.seed(seed)
        env.action_space.seed(seed)
        env.observation_space.seed(seed)
    else:
        env = MT50.train_classes[name]()
        env.seed(seed)
        env = RandomizationWrapper(env, get_subtasks(name), randomization)
        env.name = name
        env = TimeLimit(env, META_WORLD_TIME_HORIZON)
    env = gym.wrappers.ClipAction(env)
    if add_episode_monitor:
        env = wrappers.EpisodeMonitor(env)
    return env
    

if __name__ == "__main__":
    import time

    tasks_list = TASK_SEQS["cw1-push"]
    s = time.time()
    env = get_single_env(tasks_list[0], 1, "deterministic")
    print(time.time() - s)
    s = time.time()
    env = get_single_env(tasks_list[0], 1, "deterministic")
    print(time.time() - s)

    o = env.reset()
    _, _, _, _ = env.step(env.action_space.sample())
    o_new = env.reset()
    print(o)
    print(o_new)
    print(env.observation_space.shape)
    print(env.action_space.shape)