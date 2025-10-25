package config

import (
	"github.com/spf13/viper"
)

// Field name, Type, Tag
// struct field tags used for mapping during serialization/deserialization

type Config struct {
	Agent    AgentConfig    `mapstructure:"agent"`
	Database DatabaseConfig `mapstructure:"database"`
	Server   ServerConfig   `mapstructure:"server"`
	RabbitMQ RabbitMQConfig `mapstructure:"rabbitmq"`
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

type RabbitMQConfig struct {
	URL      string `mapstructure:"url"` // host:port
	Username string `mapstructure:"username"`
	Password string `mapstructure:"password"`
	Exchange string `mapstructure:"exchange"` // e.g. "events"
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

	viper.SetDefault("database.host", "localhost")
	viper.SetDefault("database.port", 5432)
	viper.SetDefault("database.user", "postgres")
	viper.SetDefault("database.password", "password")
	viper.SetDefault("database.dbname", "endpoint_security")
	viper.SetDefault("database.sslmode", "disable")

	viper.SetDefault("server.port", 8080)

	// RabbitMQ defaults
	viper.SetDefault("rabbitmq.url", "localhost:5672")
	viper.SetDefault("rabbitmq.username", "guest")
	viper.SetDefault("rabbitmq.password", "guest")
	viper.SetDefault("rabbitmq.exchange", "events")

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
