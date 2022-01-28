-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Hôte : localhost
-- Généré le : ven. 28 jan. 2022 à 21:17
-- Version du serveur : 10.5.12-MariaDB-0+deb11u1
-- Version de PHP : 8.0.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `UltimateGDPS`
--

-- --------------------------------------------------------

--
-- Structure de la table `accounts`
--

CREATE TABLE `accounts` (
  `id` int(11) NOT NULL,
  `name` varchar(15) NOT NULL,
  `email` varchar(500) NOT NULL,
  `password` varchar(1000) NOT NULL,
  `verified` tinyint(1) NOT NULL DEFAULT 0,
  `created_on` int(15) NOT NULL,
  `ip` varchar(500) NOT NULL,
  `save_data` longtext DEFAULT NULL,
  `role` int(11) NOT NULL DEFAULT 9999,
  `yt_url` varchar(255) NOT NULL DEFAULT '',
  `twitter_url` varchar(255) NOT NULL DEFAULT '',
  `twitch_url` varchar(255) NOT NULL DEFAULT '',
  `friendsreq_status` tinyint(1) NOT NULL DEFAULT 0,
  `privatemsg_status` tinyint(1) NOT NULL DEFAULT 0,
  `commenthist_status` tinyint(1) NOT NULL DEFAULT 0,
  `stars` int(11) NOT NULL DEFAULT 0,
  `demons` int(11) NOT NULL DEFAULT 0,
  `icon` int(11) NOT NULL DEFAULT 0,
  `color1` int(11) NOT NULL DEFAULT 0,
  `color2` int(11) NOT NULL DEFAULT 3,
  `icon_type` int(11) NOT NULL DEFAULT 0,
  `coins` int(11) NOT NULL DEFAULT 0,
  `user_coins` int(11) NOT NULL DEFAULT 0,
  `special` int(11) NOT NULL DEFAULT 0,
  `icon_cube` int(11) NOT NULL DEFAULT 0,
  `icon_ship` int(11) NOT NULL DEFAULT 0,
  `icon_ball` int(11) NOT NULL DEFAULT 0,
  `icon_wave` int(11) NOT NULL DEFAULT 0,
  `icon_ufo` int(11) NOT NULL DEFAULT 0,
  `icon_robot` int(11) NOT NULL DEFAULT 0,
  `icon_glow` int(11) NOT NULL DEFAULT 0,
  `creator_points` int(11) NOT NULL DEFAULT 0,
  `diamonds` int(11) NOT NULL DEFAULT 0,
  `orbs` int(11) NOT NULL DEFAULT 0,
  `completed_levels` int(11) NOT NULL DEFAULT 0,
  `icon_spider` int(11) NOT NULL DEFAULT 0,
  `icon_explosion` int(11) NOT NULL DEFAULT 0,
  `chest_b_time` int(11) NOT NULL DEFAULT 0,
  `chest_s_time` int(11) NOT NULL DEFAULT 0,
  `chest_b_count` int(11) NOT NULL DEFAULT 0,
  `chest_s_count` int(11) NOT NULL DEFAULT 0,
  `comment_color` varchar(1000) NOT NULL DEFAULT '255,255,255',
  `ban_account` tinyint(1) NOT NULL DEFAULT 0,
  `ban_account_reason` longtext DEFAULT NULL,
  `ban_lvlcomments` tinyint(1) NOT NULL DEFAULT 0,
  `ban_lvlcomment_reason` longtext DEFAULT NULL,
  `ban_profilemsg` tinyint(1) NOT NULL DEFAULT 0,
  `ban_profilemsg_reason` longtext DEFAULT NULL,
  `ban_leaderboard` tinyint(1) NOT NULL DEFAULT 0,
  `ban_leaderboard_reason` longtext DEFAULT NULL,
  `ban_lvlupload` tinyint(1) NOT NULL DEFAULT 0,
  `ban_lvlupload_reason` longtext DEFAULT NULL,
  `verify_token` varchar(1000) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `acc_comments`
--

CREATE TABLE `acc_comments` (
  `id` int(11) NOT NULL,
  `account_id` int(11) NOT NULL,
  `comment` text NOT NULL,
  `posted_on` timestamp NOT NULL DEFAULT current_timestamp(),
  `likes` int(11) NOT NULL DEFAULT 0,
  `is_spam` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `actions`
--

CREATE TABLE `actions` (
  `id` int(11) NOT NULL,
  `type` varchar(255) NOT NULL,
  `value1` varchar(500) NOT NULL DEFAULT '',
  `value2` varchar(500) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `banned_mails`
--

CREATE TABLE `banned_mails` (
  `id` int(11) NOT NULL,
  `mail_domain` varchar(500) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `blocked`
--

CREATE TABLE `blocked` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `blocked_user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `friends`
--

CREATE TABLE `friends` (
  `id` int(11) NOT NULL,
  `friend1` int(11) NOT NULL,
  `friend2` int(11) NOT NULL,
  `is_new1` int(11) NOT NULL DEFAULT 1,
  `is_new2` int(11) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `friend_requests`
--

CREATE TABLE `friend_requests` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `req_user_id` int(11) NOT NULL,
  `comment` text NOT NULL,
  `requested_on` int(11) NOT NULL,
  `is_new` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `gauntlets`
--

CREATE TABLE `gauntlets` (
  `id` int(11) NOT NULL,
  `lvl1` int(11) NOT NULL,
  `lvl2` int(11) NOT NULL,
  `lvl3` int(11) NOT NULL,
  `lvl4` int(11) NOT NULL,
  `lvl5` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `levels`
--

CREATE TABLE `levels` (
  `id` int(11) NOT NULL,
  `name` tinytext NOT NULL,
  `description` text NOT NULL,
  `level_content` longtext NOT NULL,
  `extra_content` longtext NOT NULL,
  `level_info` mediumtext NOT NULL,
  `objects` int(11) NOT NULL,
  `game_version` varchar(1000) NOT NULL,
  `binary_version` tinyint(4) NOT NULL,
  `version` int(11) NOT NULL,
  `author_id` int(11) NOT NULL,
  `official_song` int(11) NOT NULL,
  `custom_song` int(11) NOT NULL,
  `requested_rate` int(11) NOT NULL,
  `difficulty` int(11) NOT NULL DEFAULT 0,
  `coins` int(11) NOT NULL,
  `coins_verified` tinyint(1) NOT NULL DEFAULT 0,
  `downloads` int(11) NOT NULL DEFAULT 0,
  `likes` int(11) NOT NULL DEFAULT 0,
  `length` int(11) NOT NULL,
  `demon` int(11) NOT NULL DEFAULT 0,
  `demon_difficulty` int(11) NOT NULL DEFAULT 0,
  `stars` int(11) NOT NULL DEFAULT 0,
  `featured` int(11) NOT NULL DEFAULT 0,
  `auto` tinyint(1) NOT NULL DEFAULT 0,
  `epic` tinyint(1) NOT NULL DEFAULT 0,
  `password` int(11) NOT NULL,
  `original` tinyint(4) NOT NULL,
  `upload_date` varchar(1000) NOT NULL DEFAULT current_timestamp(),
  `update_date` varchar(100) DEFAULT '0',
  `copy` int(11) NOT NULL DEFAULT 0,
  `dual_mode` int(11) NOT NULL,
  `ldm` int(11) NOT NULL,
  `unlisted` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `lvl_comments`
--

CREATE TABLE `lvl_comments` (
  `id` int(11) NOT NULL,
  `author_id` int(11) NOT NULL,
  `comment` text NOT NULL,
  `level_id` int(11) NOT NULL,
  `likes` int(11) NOT NULL DEFAULT 0,
  `uploaded_on` bigint(20) NOT NULL DEFAULT current_timestamp(),
  `percent` int(11) NOT NULL,
  `is_spam` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `map_packs`
--

CREATE TABLE `map_packs` (
  `id` int(11) NOT NULL,
  `name` varchar(250) NOT NULL,
  `levels` varchar(532) NOT NULL,
  `stars` int(11) NOT NULL,
  `coins` int(11) NOT NULL,
  `difficulty` int(11) NOT NULL,
  `color` varchar(12) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `private_messages`
--

CREATE TABLE `private_messages` (
  `id` int(11) NOT NULL,
  `from_id` int(11) NOT NULL,
  `to_id` int(11) NOT NULL,
  `subject` text NOT NULL,
  `body` text NOT NULL,
  `sent_on` int(11) NOT NULL,
  `is_new` int(11) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `quests`
--

CREATE TABLE `quests` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `type` int(11) NOT NULL,
  `amount` int(11) NOT NULL,
  `reward` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `register_ips`
--

CREATE TABLE `register_ips` (
  `ip` varchar(15) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `roles`
--

CREATE TABLE `roles` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL,
  `badge` int(11) NOT NULL DEFAULT 0,
  `perm_rate` tinyint(1) NOT NULL DEFAULT 0,
  `perm_epic` tinyint(1) NOT NULL DEFAULT 0,
  `perm_suggest` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `songs`
--

CREATE TABLE `songs` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL,
  `author_id` int(11) NOT NULL,
  `author_name` text NOT NULL,
  `size` varchar(50) NOT NULL,
  `disabled` tinyint(1) NOT NULL DEFAULT 0,
  `download_link` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `accounts`
--
ALTER TABLE `accounts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `stars` (`stars`),
  ADD KEY `verified` (`verified`);

--
-- Index pour la table `acc_comments`
--
ALTER TABLE `acc_comments`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `actions`
--
ALTER TABLE `actions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `type` (`type`),
  ADD KEY `acc_id` (`value1`),
  ADD KEY `lvl_id` (`value2`);

--
-- Index pour la table `banned_mails`
--
ALTER TABLE `banned_mails`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `blocked`
--
ALTER TABLE `blocked`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `friends`
--
ALTER TABLE `friends`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `friend_requests`
--
ALTER TABLE `friend_requests`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `gauntlets`
--
ALTER TABLE `gauntlets`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `levels`
--
ALTER TABLE `levels`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `lvl_comments`
--
ALTER TABLE `lvl_comments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `level_id` (`level_id`);

--
-- Index pour la table `map_packs`
--
ALTER TABLE `map_packs`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `private_messages`
--
ALTER TABLE `private_messages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `from_id` (`from_id`),
  ADD KEY `to_id` (`to_id`);

--
-- Index pour la table `quests`
--
ALTER TABLE `quests`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `register_ips`
--
ALTER TABLE `register_ips`
  ADD PRIMARY KEY (`ip`);

--
-- Index pour la table `roles`
--
ALTER TABLE `roles`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `songs`
--
ALTER TABLE `songs`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `accounts`
--
ALTER TABLE `accounts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `acc_comments`
--
ALTER TABLE `acc_comments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `actions`
--
ALTER TABLE `actions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `banned_mails`
--
ALTER TABLE `banned_mails`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `blocked`
--
ALTER TABLE `blocked`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `friends`
--
ALTER TABLE `friends`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `friend_requests`
--
ALTER TABLE `friend_requests`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `gauntlets`
--
ALTER TABLE `gauntlets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `levels`
--
ALTER TABLE `levels`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `lvl_comments`
--
ALTER TABLE `lvl_comments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `map_packs`
--
ALTER TABLE `map_packs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `private_messages`
--
ALTER TABLE `private_messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `quests`
--
ALTER TABLE `quests`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `roles`
--
ALTER TABLE `roles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
