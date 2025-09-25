package config

import (
	"github.com/spf13/viper"
)

type Config struct {
	Agent    AgentConfig    `mapstructure:"agent"`
	Database DatabaseConfig `mapstructure:"database"`
	Server   ServerConfig   `mapstructure:"server"`
}

type AgentConfig struct {
	ID                string `mapstructure:"id"`
	Name              string `mapstructure:"name"`
	Version           string `mapstructure:"version"`
	CollectorInterval int    `mapstructure:"collector_interval"`
	LogLevel          string `mapstructure:"log_level"`
}

type DatabaseConfig struct {
	Host     string `mapstructure:"host"`
	Port     int    `mapstructure:"port"`
	User     string `mapstructure:"user"`
	Password string `mapstructure:"password"`
	DBName   string `mapstructure:"dbname"`
	SSLMode  string `mapstructure:"sslmode"`
}

type ServerConfig struct {
	Port int `mapstructure:"port"`
}

func LoadConfig() (*Config, error) {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(".")
	viper.AddConfigPath("./config")

	// Set defaults
	viper.SetDefault("agent.id", "windows-agent-001")
	viper.SetDefault("agent.name", "Windows Security Agent")
	viper.SetDefault("agent.version", "1.0.0")
	viper.SetDefault("agent.collector_interval", 30)
	viper.SetDefault("agent.log_level", "info")

	viper.SetDefault("database.host", "ep-super-pine-a1glsjev-pooler.ap-southeast-1.aws.neon.tech")
	viper.SetDefault("database.port", 5432)
	viper.SetDefault("database.user", "neondb_owner")
	viper.SetDefault("database.password", "npg_vsHuI17fBYML")
	viper.SetDefault("database.dbname", "neondb")
	viper.SetDefault("database.sslmode", "require")

	viper.SetDefault("server.port", 8080)

	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			return nil, err
		}
	}

	var config Config
	if err := viper.Unmarshal(&config); err != nil {
		return nil, err
	}

	return &config, nil
}
