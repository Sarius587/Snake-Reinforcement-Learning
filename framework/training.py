from framework.core import Transition


class Training:

    def __init__(self, create_env_func, agent):
        self.create_env_func = create_env_func
        self.agent = agent

    def train(self, max_steps=100_000, instances=1, visualize=False, plot_func=None, max_subprocesses=0):
        if max_subprocesses == 0:
            self._sp_train(max_steps, instances, visualize, plot_func)

    def evaluate(self, max_steps=10_000, visualize=False, plot_func=None):
        self.agent.training = False
        env = self.create_env_func()
        state = env.reset()
        episode_reward = 0
        episode_rewards = []
        episode_steps = []

        for step in range(max_steps):
            if visualize:
                env.render()
            action = self.agent.act(state)
            next_state, reward, done, _ = env.step(action)
            episode_reward += reward
            if done:
                episode_rewards.append(episode_reward)
                episode_steps.append(step)
                episode_reward = 0
                if plot_func:
                    plot_func(episode_rewards, episode_steps)
                state = env.reset()
            else:
                state = next_state

        if plot_func:
            plot_func(episode_rewards, episode_steps, True)

    def _sp_train(self, max_steps, instances, visualize, plot):
        """Trains using a single process."""
        # Keep track of rewards per episode per instance
        episode_reward_sequences = [[] for i in range(instances)]
        episode_step_sequences = [[] for i in range(instances)]
        episode_rewards = [0] * instances

        # Create and initialize environment instances
        envs = [self.create_env_func() for i in range(instances)]
        states = [env.reset() for env in envs]
        print(states[0])

        for step in range(max_steps):
            for i in range(instances):
                if visualize:
                    envs[i].render()
                action = self.agent.act(states[i])
                next_state, reward, done, _ = envs[i].step(action)
                self.agent.push_observation(Transition(states[i], action, reward, None if done else next_state))
                episode_rewards[i] += reward
                if done:
                    episode_reward_sequences[i].append(episode_rewards[i])
                    episode_step_sequences[i].append(step)
                    episode_rewards[i] = 0
                    if plot: plot(episode_reward_sequences, episode_step_sequences)
                    states[i] = envs[i].reset()
                else:
                    states[i] = next_state
            # Perform one step of the optimization
            self.agent.train(step)

        if plot:
            plot(episode_reward_sequences, episode_step_sequences, done=True)